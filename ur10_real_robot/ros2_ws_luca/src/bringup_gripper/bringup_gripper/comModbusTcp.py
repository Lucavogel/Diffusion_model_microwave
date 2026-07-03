#!/usr/bin/env python3
"""
Module comModbusTcp: defines a class which communicates with
OnRobot Grippers using the Modbus/TCP protocol.
"""

import sys
import threading

try:
    from pymodbus.client import ModbusTcpClient
    DEVICE_ID_KWARG = "device_id"
except ImportError:
    from pymodbus.client.sync import ModbusTcpClient
    DEVICE_ID_KWARG = "unit"


class Communication:

    def __init__(self, dummy=False, logger=None):
        self.client = None
        self.dummy = dummy
        self.logger = logger
        self.lock = threading.Lock()

    def _log_info(self, message):
        if self.logger is not None:
            self.logger.info(message)

    def _log_error(self, message):
        if self.logger is not None:
            self.logger.error(message)

    def _device_kwargs(self):
        return {DEVICE_ID_KWARG: 65}

    def _read_holding_registers(self, address, count):
        return self.client.read_holding_registers(
            address=address,
            count=count,
            **self._device_kwargs(),
        )

    def _write_register(self, address, value):
        return self.client.write_register(
            address=address,
            value=value,
            **self._device_kwargs(),
        )
#--------------------------------------------------------------------------
    def connectToDevice(self, ip, port):
        """Connects to the client.
           The method takes the IP address and port number
           (as a string, e.g. '127.0.0.1' and '502') as arguments.
        """
        if self.dummy:
            self._log_info(sys._getframe().f_code.co_name)
            return

        self.client = ModbusTcpClient(
            ip,
            port=port,
            timeout=1)
        connected = self.client.connect()
        if not connected:
            self._log_error(f"Failed to connect to {ip}:{port}")
        return connected
#--------------------------------------------------------------------------
    def disconnectFromDevice(self):
        """Closes connection."""
        if self.dummy:
            self._log_info(sys._getframe().f_code.co_name)
            return

        if self.client is not None:
            self.client.close()
#--------------------------------------------------------------------------
    def setProximityOffset(self, ProxOffsets):

        with self.lock:
            self._write_register(address=5, value=ProxOffsets[0])
            self._write_register(address=6, value=ProxOffsets[1])
#--------------------------------------------------------------------------
    def sendCommand(self, message):
        """Sends a command to the Gripper.
           The method takes a list of uint8 as an argument.
        """
        if self.dummy:
            self._log_info(sys._getframe().f_code.co_name)
            return

        # Sends the command to the device
        if message != []:
            with self.lock:
                self._write_register(address=0, value=message[0])
                self._write_register(address=2, value=message[1])
                self._write_register(address=3, value=message[2])
                self._write_register(address=4, value=message[3])
#--------------------------------------------------------------------------
    def getStatus(self):
        """Sending a request to the device to get the status.
        """
        response1 = [0] * 2
        response2 = [0] * 26
        response3 = [0] * 1
        if self.dummy:
            self._log_info(sys._getframe().f_code.co_name)
            return response1 + response2 + response3

        with self.lock:
            # Get status from the device (address 5 and 6)
            response1 = self._read_holding_registers(
                address=5, count=2).registers


            # get status from the device (address 257 to 282)
            response2 = self._read_holding_registers(
                address=257, count=26).registers

            # Get status from the device (address 0)
            response3 = self._read_holding_registers(
                address=0, count=1).registers

        # Output the result
        return response1 + response2 + response3
