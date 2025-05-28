import logging
import asyncio

logging.basicConfig(level=logging.INFO)

from plc4py.PlcDriverManager import PlcDriverManager
from plc4py.spi.values.PlcValues import PlcBOOL, PlcINT

connection_string = "modbus://127.0.0.1:502"
driver_manager = PlcDriverManager()

async def readaddr(addr):
    async with driver_manager.connection(connection_string) as connection:
        with connection.read_request_builder() as builder:
            builder.add_item("rd", "4x%05d" % (1+addr,))
            request = builder.build()
        response = await connection.execute(request)
        print(f"Response code: {response.response_code}")
        item = response.get_plc_value('rd')
        print(addr,item)
        return item.get_int()

async def readaddr_n(addr, n):
    async with driver_manager.connection(connection_string) as connection:
        with connection.read_request_builder() as builder:
            builder.add_item("rd", "4x%05d[%d]" % (1+addr,n))
            request = builder.build()
        response = await connection.execute(request)
        print(f"Response code: {response.response_code}")
        lst = [item for item in response.get_plc_value('rd').get_list()]        
        print(addr,lst)
        return lst

async def writeaddr(addr, n):
    async with driver_manager.connection(connection_string) as connection:
        with connection.write_request_builder() as builder:
            builder.add_item("ctrl", "4x%05d" % (1+addr,), PlcINT(n))
            request = builder.build()
        response = await connection.execute(request)
        print(f"Response code: {response.response_code}")

asyncio.run(writeaddr(129,0))
asyncio.run(writeaddr(130,0))
