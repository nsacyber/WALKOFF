#!/usr/bin/env bash
set -e

if [ "$1" = 'postgres' ] && [ "$(id -u)" = '0' ]; then
	[[ ${POD_NAME} =~ -([0-9]+)$ ]] || exit 1
	ordinal=${BASH_REMATCH[1]}
	if [ $STATEFUL_TYPE == "master" ]; then
		node_id=$((${ordinal} + 1))
		service=${MASTER_SERVICE}
	else
		node_id=$((${ordinal} + 100))
		service=${POD_NAME}
	fi

	if [ ${STANDBY_ENABLED} ]; then
		sed \
			-e "s|^#cluster=.*$|cluster=default|" \
			-e "s|^#node=.*$|node=${node_id}|" \
			-e "s|^#node_name=.*$|node_name=${POD_NAME}|" \
			-e "s|^#conninfo=.*$|conninfo='host=${service} dbname=repmgr user=repmgr password=${REPMGR_PASSWORD} application_name=repmgrd'|" \
			-e "s|^#use_replication_slots=.*$|use_replication_slots=1|" \
			/etc/repmgr.conf.tpl > /etc/repmgr.conf
	fi

	if [ ${STATEFUL_TYPE} == "master" ]; then
		if [ ! -s "${PGDATA}/PG_VERSION" ]; then
			docker-entrypoint.sh "$@" --boot

			sed -i \
				-e "s|^listen_addresses = .*|listen_addresses = '*'|" \
				${PGDATA}/postgresql.conf

			host_type="host"
			options=""

			if [ -f "/certs/server.key" ]; then
				host_type="hostssl"

				if [ -f "/certs/postgresql.key" ]; then
					options="clientcert=1"
				fi

				# Server Certificate
				cp -f /certs/{server,root}.* ${PGDATA}/
				chown postgres:postgres ${PGDATA}/{root,server}.*
				chmod -R 0600 ${PGDATA}/{root,server}.*

				# Client Certificate
				mkdir -p /home/postgres/.postgresql/
				cp -f /certs/{postgresql,root}.* /home/postgres/.postgresql/
				chown -R postgres:postgres /home/postgres
				chmod -R 0600 /home/postgres/.postgresql/*

				sed -i \
					-e "s|^#ssl = .*|ssl = on|" \
					-e "s|^#ssl_ciphers = .*|ssl_ciphers = 'HIGH'|" \
					-e "s|^#ssl_cert_file = .*|ssl_cert_file = 'server.crt'|" \
					-e "s|^#ssl_key_file = .*|ssl_key_file = 'server.key'|" \
					-e "s|^#ssl_ca_file = .*|ssl_ca_file = 'root.crt'|" \
					-e "s|^#ssl_crl_file = .*|ssl_crl_file = 'root.crl'|" \
					${PGDATA}/postgresql.conf

				sed -i \
					-E "s|^host([ \\t]+all){3}.*|hostnossl   all   all   all   reject\n${host_type}   all   all   all   md5   ${options}|" \
					${PGDATA}/pg_hba.conf
			fi
		fi

		if [ ${STANDBY_ENABLED} ] && [ -n "grep -q '#hot_standby' ${PGDATA}/postgresql.conf" ]; then
			sed -i \
				-e "s|^#hot_standby = .*|hot_standby = on|" \
				-e "s|^#wal_level = .*|wal_level = hot_standby|" \
				-e "s|^#max_wal_senders = .*|max_wal_senders = 10|" \
				-e "s|^#max_replication_slots = .*|max_replication_slots = 10|" \
				-e "s|^#archive_mode = .*|archive_mode = on|" \
				-e "s|^#archive_command = .*|archive_command = '/bin/true'|" \
				-e "s|^#shared_preload_libraries = .*|shared_preload_libraries = 'repmgr_funcs'|" \
				${PGDATA}/postgresql.conf

			cat >> ${PGDATA}/pg_hba.conf <<-EOF

			# repmgr
			${host_type}   repmgr        repmgr   all   md5   ${options}
			${host_type}   replication   repmgr   all   md5   ${options}
			EOF

			gosu postgres pg_ctl start -w

			gosu postgres psql <<-EOF
			CREATE USER repmgr SUPERUSER LOGIN ENCRYPTED PASSWORD '${REPMGR_PASSWORD}';
			CREATE DATABASE repmgr OWNER repmgr;
			EOF

			while ! gosu postgres pg_isready --host ${MASTER_SERVICE} --quiet
			do
				sleep 1
			done

			gosu postgres repmgr master register

			gosu postgres psql -U repmgr -d repmgr <<-EOF
			ALTER TABLE repmgr_default.repl_monitor SET UNLOGGED;
			EOF

			gosu postgres pg_ctl -w stop
		fi
	fi

	if [ ${STATEFUL_TYPE} == "standby" ]; then
		if [ ! -s "${PGDATA}/PG_VERSION" ]; then
			while ! gosu postgres pg_isready --host ${MASTER_SERVICE} --quiet
			do
				sleep 1
			done

			mkdir -p "$PGDATA"
			chown -R postgres "$PGDATA"
			chmod 700 "$PGDATA"

			if [ -f "/certs/root.crt" ]; then
				# Client Certificate
				mkdir -p /home/postgres/.postgresql/
				cp -f /certs/{postgresql,root}.* /home/postgres/.postgresql/
				chown -R postgres:postgres /home/postgres
				chmod -R 0600 /home/postgres/.postgresql/*
			fi

			gosu postgres repmgr \
				--dbname="host=${MASTER_SERVICE} dbname=repmgr user=repmgr password=${REPMGR_PASSWORD}" \
				standby clone

			if [ -f "/certs/server.crt" ]; then
				# Server Certificate
				cp -f /certs/{server,root}.* ${PGDATA}/
				chown postgres:postgres ${PGDATA}/{root,server}.*
				chmod -R 0600 ${PGDATA}/{root,server}.*
			fi

			gosu postgres pg_ctl -w start

			while ! pg_isready --host 127.0.0.1 --quiet
			do
				sleep 1
			done

			gosu postgres repmgr standby register

			gosu postgres pg_ctl -w stop
		fi
	fi

	if [ -f "/certs/server.key" ]; then
		# Server Certificate
		cp -f /certs/{server,root}.* ${PGDATA}/
		chown postgres:postgres ${PGDATA}/{root,server}.*
		chmod -R 0600 ${PGDATA}/{root,server}.*
	fi

	if [ -f "/certs/root.crt" ]; then
		# Client Certificate
		mkdir -p /home/postgres/.postgresql/
		cp -f /certs/{postgresql,root}.* /home/postgres/.postgresql/
		chown -R postgres:postgres /home/postgres
		chmod -R 0600 /home/postgres/.postgresql/*
	fi

	exec docker-entrypoint.sh "$@" & pid=$!

	while ! gosu postgres pg_isready --host ${service} --quiet
	do
		sleep 1
	done

	if [ ${STANDBY_ENABLED} ]; then
		supervisorctl start repmgrd
	fi

	wait ${pid}
	exit 0
fi

if [ "$1" = 'repmgrd' ] && [ "$(id -u)" = '0' ]; then
	exec gosu postgres "$@"
fi

if [ "$1" = 'cleanup' ]; then
	if [ ${STATEFUL_TYPE} == "master" ]; then
		if [ ${STANDBY_ENABLED} ]; then
			while true
			do
				sleep 3600

				if pg_isready --host 127.0.0.1 --quiet; then
					gosu postgres repmgr --keep-history=1 cluster cleanup || true
				fi
			done
		fi
	fi

	exit 0
fi

exec "$@"
