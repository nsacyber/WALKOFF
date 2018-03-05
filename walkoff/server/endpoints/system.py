import psutil
from flask_jwt_extended import jwt_required

from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.server.returncodes import *

metric_symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
bytes_prefix = {}
for i, symbol in enumerate(metric_symbols):
    bytes_prefix[symbol] = 1 << (i + 1) * 10


def humanize_bytes(bytes):
    for symbol in reversed(metric_symbols):
        if bytes >= bytes_prefix[symbol]:
            value = float(bytes) / bytes_prefix[symbol]
            return str(round(value, 2)) + symbol
    return '{}B'.format(bytes)


def get_system_usage():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('metrics', ['read']))
    def __func():
        return _system_resource_usage(), SUCCESS

    return __func()


def _system_resource_usage():
    result = {}

    cpu_times = psutil.cpu_percent(interval=None, percpu=True)
    result["cpu"] = {'percents': cpu_times}

    mem = psutil.virtual_memory()
    memory_result = {'total': humanize_bytes(mem.total),
                     "available": humanize_bytes(mem.available),
                     "percent": mem.percent}
    result['memory'] = memory_result

    disk = psutil.disk_usage("/")
    disk_result = {"total": humanize_bytes(disk.total),
                   "used": humanize_bytes(disk.used),
                   "free": humanize_bytes(disk.free),
                   "percent": disk.percent}
    result['disk'] = disk_result

    net = psutil.net_io_counters()
    net_result = {"bytes_sent": humanize_bytes(net.bytes_sent),
                  "bytes_received": humanize_bytes(net.bytes_recv),
                  "packets_sent": net.packets_sent,
                  "packets_received": net.packets_recv,
                  "error_in": net.errin,
                  "error_out": net.errout,
                  "dropped_in": net.dropin,
                  "dropped_out": net.dropout}
    result['net'] = net_result

    return result
