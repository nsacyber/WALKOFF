#!/usr/bin/env python

import json
import os
from timeit import default_timer as timer

import falcon
import yaml
from jsonschema import validate, ValidationError
import walkoff.config
from apps import App
from walkoff.appgateway import cache_apps, get_app
from walkoff.appgateway.accumulators import ExternallyCachedAccumulator
from walkoff.appgateway.apiutil import UnknownFunction
from walkoff.cache import make_cache
from walkoff.executiondb import ExecutionDatabase
from walkoff.helpers import ExecutionError
from walkoff.worker.action_exec_strategy import LocalActionExecutionStrategy, ExecutableContext
import jwt
import logging


app_name = os.environ.get('APP_NAME')


def make_logger():
    logger_ = logging.getLogger('{}_runtime'.format(app_name))
    logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))
    return logger_

logger = make_logger()


app_creation_lock_prefix = 'app_creation_lock'
app_instance_created_set_prefix = 'app_instance_created_set'
cache_separator = ':'
app_instance_set_name = '{}{}{}'.format(app_instance_created_set_prefix, cache_separator, app_name)

def parse_openapi(path):
    logger.debug('Parsing OpenAPI file at {}'.format(path))
    try:
        with open(path) as openapi:
            openapi = yaml.safe_load(openapi)
            definitions = openapi['definitions']
            schema = definitions['ExecutionContext']

            for position, replacement in (('workflow_context', 'WorkflowContext'), ('executable_context', 'ExecutableContext')):
                schema['properties'][position] = definitions[replacement]

            schema['properties']['arguments']['items'] = definitions['Argument']
        return schema
    except (OSError, IOError) as e:
        logger.exception('Could not parse OpenAPI specification', level=logging.FATAL)
        raise

def make_redis():
    redis_host = os.environ.get('REDIS_HOST')
    redis_port = os.environ.get('REDIS_PORT', 6379)
    options = os.environ.get('REDIS_OPTIONS', {})
    config = {'host': redis_host, 'port': redis_port}
    config.update(options)
    logger.info('Creating Redis Cache with options {}'.format(config))
    redis_cache = make_cache(config)
    try:
        redis_cache.ping()
    except Exception as e:
        logger.exception('Could not connect to Redis cache.', level=logging.FATAL)
        raise
    return redis_cache

def make_execution_db():
    execution_db_path = os.environ.get('EXECUTION_DB_PATH')
    execution_db_type = os.environ.get('EXECUTION_DB_TYPE', 'postgresql')
    logging.info('Connecting to Execution DB with type {} at {}'.format(execution_db_type, execution_db_path))
    execution_db = ExecutionDatabase(execution_db_type, execution_db_path)
    return execution_db

app_path = os.environ.get('APP_PATH', './app')
cache_apps(app_path)
walkoff.config.load_app_apis(app_path)
execution_post_schema = parse_openapi(os.environ.get('OPENAPI_PATH', 'api.yaml'))

redis_cache = make_redis()
make_execution_db()


class ActionExecution(object):

    def __init__(self, strategy, accumulator):
        self.strategy = strategy
        self.accumulator = accumulator

    def on_post(self, req, resp, workflow_exec_id, action_exec_id):

        data = req.json
        try:
            validate(data, execution_post_schema)
        except ValidationError as e:
            logger.error(
                'Schema validation error while parsing execution request for workflow_id {}, action_id {}'.format(
                    workflow_exec_id,
                    action_exec_id
                )
            )
            raise falcon.HTTPBadRequest('Invalid execution request', str(e))
        workflow_context = {'workflow_{}'.format(key): value for key, value in data['workflow_context'].items()}
        workflow_context['workflow_execution_id'] = workflow_exec_id
        self.accumulator.set_key(workflow_exec_id)
        action_context = data['executable_context']
        executable_context = ExecutableContext(
            action_context['type'],
            app_name,
            action_context['name'],
            action_context['id']
        )
        if 'device_id' in action_context:
            app_instance = self.create_device(workflow_context, action_context['device_id'])
        else:
            logger.debug('App instance creation not required.')
            app_instance = None

        arguments = {arg['name']: arg['value'] for arg in data['arguments']}

        try:
            logger.info('Executing {}'.format(str(executable_context)))
            result = self.strategy.execute_from_context(
                executable_context,
                self.accumulator,
                arguments,
                instance=app_instance
            )
            if executable_context.is_action():
                result.set_default_status(app_name, executable_context.executable_name)
                result_status = result.status
            else:
                result_status = 'Success'
        except ExecutionError as e:
            logger.exception('Unhandled exception while executing {}'.format(str(executable_context)))
            result_status = 'UnhandledException'
        except UnknownFunction:
            logger.error('Unknown function {} of type {}'.format(
                executable_context.executable_name,
                executable_context.type)
            )
            raise falcon.HTTPNotFound(
                title='Unknown {}'.format(executable_context.type),
                description='Unknown {} {}'.format(executable_context.type, executable_context.executable_name)
            )

        result = {'status': result_status, 'result_key': self.accumulator.format_key(str(executable_context.id))}
        logger.info('Result of executing {}: {}'.format(str(executable_context), result))
        resp.media = result

    @staticmethod
    def format_app_instance_key(workflow_execution_id, device_id):
        return '{}{}{}'.format(
            workflow_execution_id,
            cache_separator,
            device_id
        )

    def create_device(self, workflow_context, device_id):
        workflow_exec_id = workflow_context['workflow_execution_id']
        logger.info('Creating app instance for workflow {}, device {}'.format(workflow_exec_id, device_id))
        redis_key = ActionExecution.format_app_instance_key(workflow_exec_id, device_id)
        app_class = get_app(app_name)
        if not redis_cache.cache.sismember(app_instance_set_name, redis_key):
            #If workflows become parallelized, this will need to be locked
            logger.info('Creating new app instance')
            app_instance = app_class(app_name, device_id, workflow_context)
            redis_cache.cache.sadd(app_instance_set_name, redis_key)
            return app_instance
        else:
            logger.debug('Using existing app instance')
            return App.from_cache(app_name, device_id, workflow_context)


class WorkflowExecution(object):

    def on_delete(self, req, resp, workflow_exec_id):
        scan_pattern = WorkflowExecution.format_scan_pattern(workflow_exec_id)
        for key in redis_cache.cache.sscan_iter(app_instance_set_name, match=scan_pattern):
            logger.debug('Deleting entry {} from Redis set {}'.format(key, app_instance_set_name))
            redis_cache.cache.srem(app_instance_set_name, key)
        resp.status = falcon.HTTP_204

    @staticmethod
    def format_scan_pattern(workflow_exec_id):
        return '{}{}*'.format(workflow_exec_id, cache_separator)

class Health(object):

    no_auth = True

    def on_get(self, req, resp):
        try:
            start = timer()
            redis_cache.ping()
            end = timer()
            resp.media = {
                'cache': [
                    {'test_name': 'pinging',
                     'result': 'pass',
                     'time': str(end-start)
                     }
                ]
            }

        except Exception as e:
            result = {
                'cache': [
                    {'test_name': 'pinging',
                     'result': 'failed',
                     'reason': 'exception raised'
                     }
                ]
            }
            logger.exception('App is unhealthy!')
            resp.media = result
            resp.status = falcon.HTTP_400


class JsonMiddleware(object):
    def process_request(self, req, resp):
        """Middleware request"""
        if not req.content_length:
            return
        try:
            req.json = json.loads(req.stream.read().decode('utf-8'))
        except UnicodeDecodeError:
            logger.error('Could not decode request as UTF-8')
            raise falcon.HTTPBadRequest("Invalid encoding", "Could not decode as UTF-8")
        except ValueError:
            logger.error('Invalid JSON found')
            raise falcon.HTTPBadRequest("Malformed JSON", "Syntax error")


class AuthMiddleware(object):

    def __init__(self, secret):
        self.secret = secret

    def process_resource(self, req, resp, resource, params):
        if getattr(resource, 'no_auth', False):
            return

        token = req.get_header('Authorization')
        if token is None:
            logger.error('No Authorization header provided')
            description = 'Please provide an auth token as part of the request.'
            raise falcon.HTTPUnauthorized('Auth token required', description)

        token_parts = token.split()
        if token_parts[0] != 'Bearer':
            logger.error('Bearer was no part of Authorization header')
            description = 'Token must be a header of the form Authorization: Bearer <token>.'
            raise falcon.HTTPUnauthorized('Auth token improperly formatted', description)
        token = token_parts[1]
        if not self._token_is_valid(token):
            logger.error('Authorization token was invalid')
            description = 'The provided auth token is not valid. Please request a new token and try again.'

            raise falcon.HTTPUnauthorized('Authentication required', description)

    def _token_is_valid(self, token):
        try:
            options = {'verify_exp': True}
            jwt.decode(token, self.secret, verify='True', algorithms=['HS256'], options=options)
            return True
        except jwt.DecodeError:
            return False


jwt_secret = os.environ.get('JWT_SECRET')

api = application = falcon.API(middleware=[JsonMiddleware(), AuthMiddleware(jwt_secret)])

accumulator = ExternallyCachedAccumulator(redis_cache, 'null')
action_executions = ActionExecution(LocalActionExecutionStrategy(fully_cached=True), accumulator)
workflow_executions = WorkflowExecution()
health_resource = Health()

api.add_route(
    '/workflows/{workflow_exec_id:uuid}/actions/{action_exec_id:uuid}',
    action_executions)
api.add_route('/workflows/{workflow_exec_id:uuid}', workflow_executions)
api.add_route('/health', health_resource)

logger.info('Beginning server')