import datetime
import ipaddress
import asyncio

from walkoff_app_sdk.app_base import AppBase


class IPAddrUtils(AppBase):
    __version__ = "1.0.0"
    app_name = "ip_addr_utils"

    def __init__(self, redis, logger):
        super().__init__(redis, logger)

    async def set_timestamp(self):
        timestamp = '{:%Y-%m-%d_%H-%M-%S}'.format(datetime.datetime.now())
        return timestamp

    async def cidr_to_array(self, ip_array):
        results = []
        for ip_range in ip_array:
            for ip in ipaddress.IPv4Network(ip_range):
                results.append(str(ip))
        return results


if __name__ == "__main__":
    asyncio.run(IPAddrUtils.run())
