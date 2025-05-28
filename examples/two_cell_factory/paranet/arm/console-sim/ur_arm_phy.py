import sys
import time

import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp

server = modbus_tcp.TcpServer(port=8502)
server.start()
slave = server.add_slave(1)
slave.add_block('0', cst.HOLDING_REGISTERS, 128, 384)

slave.set_values('0', 256, [15,19,7])

while True:
    values = slave.get_values('0', 128, 4)
    if values[0] != 0:
        act = values[0]
        print(f'SIM ACTION {act} - start')
        slave.set_values('0', 129, [0])
        time.sleep(3)
        slave.set_values('0', 129, [act])
        print(f'SIM ACTION {act} - end')
    time.sleep(0.1)
