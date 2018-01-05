from flask_jwt_extended import jwt_required

from walkoff.server.returncodes import *
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions


def get_resource_usage():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('metrics', ['read']))
    def __func():
        return _resource_usage(), SUCCESS

    return __func()

def _resource_usage():
    import psutil

    result = {}
    #Cpu usage by processor
    cpuTimes = psutil.cpu_percent(interval=None, percpu=True)
    result["cpuTimes"] = cpuTimes

    #Memory Usage and Percentage used
    mem = psutil.virtual_memory()
    result["totalMemory"] = mem.total
    result["availableMemory"] = mem.available
    result["percentageMemory"] = mem.available/mem.total

    #Disk Usage
    disk = psutil.disk_usage("/")
    result["diskTotal"] = disk.total
    result["diskUsed"] = disk.used
    result["diskFree"] = disk.free
    result["diskPercent"] = disk.percent

    #Network Usage
    net = psutil.net_io_counters()
    result["netBytesSent"] = net.bytes_sent
    result["netBytesRecieved"] = net.bytes_recv
    result["netPacketsSent"] = net.packets_sent
    result["netPacketsRecieved"] = net.packets_recv
    result["netErrIn"] = net.errin
    result["netErrOut"] = net.errout
    result["netDropIn"] = net.dropin
    result["netDropOut"] = net.dropout

    return result