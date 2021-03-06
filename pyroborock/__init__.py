import base64
import json
import os
import sys
import asyncio
import threading
import logging
import tinytuya
import time

from miio.vacuum import Vacuum
from miio.exceptions import DeviceError, DeviceException, RecoverableError

from typing import Any, Dict, List

from Crypto.Cipher import AES
from subprocess import Popen, PIPE


#Message keys
DISCONNECTED = 'disconnected'
CONNECTED = 'connected'
READY = 'ready'
RESPONSE = 'response'

TYPE = 'type'

debug = False


class TuyaProtocol:
    def __init__(self, ip, token, device_id, debug=False):
        self.__id = 9999

        self.ip = ip
        self.token = token
        self.device_id = device_id

        self.responses = {}
        self.is_connected_to_roborock = False
        self.is_ready_for_comms = False

        self.tuya_device = VacuumDevice(device_id, ip, token)
        self.tuya_device.set_version(3.3)

    def _ob_exists_recursive(self, keys, ob, i=0):
        if keys[i] in ob:
            if i == len(keys) - 1:
                return True
            else:
                return self._ob_exists_recursive(keys, ob[keys[i]], i+1)
        else:
            return False

    def _decode_message(self, message):
        if message is None:
            return None

        if self._ob_exists_recursive(['dps', '102'], message):
            resp = message['dps']['102']
            if resp:
                decoded = base64.b64decode(resp.encode('utf-8'))
                return json.loads(decoded)

        return None

    @property
    def _id(self) -> int:
        """Increment and return the sequence id."""
        self.__id -= 1
        if self.__id < 1:
            self.__id = 9998
        return self.__id

    @property
    def raw_id(self):
        return self.__id

    def _connect(self):
        data = self.tuya_device.status()
        self.is_connected_to_roborock = True
        self.is_ready_for_comms = True

    def _create_request(
        self, command: str, parameters: Any, extra_parameters: Dict = None
    ):
        """Create request payload."""
        request = {"id": self._id, "method": command}

        if parameters is not None:
            request["params"] = parameters
        else:
            request["params"] = []

        if extra_parameters is not None:
            request = {**request, **extra_parameters}

        return request

    def send(
        self,
        command: str,
        parameters = None,
        retry_count: int = 3,
        *,
        extra_parameters = None
    ):
        is_ready = self.is_connected_to_roborock and self.is_ready_for_comms

        if not is_ready:
            self._connect()

        req = self._create_request(command, parameters, extra_parameters)
        req_id = req['id']
        req = json.dumps(req)
        tuya_req = base64.b64encode(req.replace(' ', '').encode('utf-8')).decode('utf-8')

        retries = 5
        response = None
        # Retry if the response is None
        while response is None and retries > 0:
            response = self.tuya_device.set_value(101, tuya_req)
            response = self._decode_message(response)

            if response is None:
                retries -= 1
                time.sleep(1)

        if response is not None:
            return response['result']

        return None


    def close(self):
        self.tuya_node_wrapper.disconnect()

class Roborock(Vacuum):
    """Main class representing the vacuum."""

    def __init__(
        self, ip: str, token: str, device_id: str, debug: int = 0
    ) -> None:
        super().__init__(ip, token, debug=debug)
        self._protocol = TuyaProtocol(ip, token, device_id, debug=debug != 0)

    def close(self):
        self._protocol.close()

class VacuumDevice(tinytuya.XenonDevice):
    def __init__(self, dev_id, address, local_key=None):
        dev_type = 'default'
        super(VacuumDevice, self).__init__(dev_id, address, local_key, dev_type)

    def status(self):
        """Return device status."""
        payload = self.generate_payload(tinytuya.DP_QUERY)

        data = self._send_receive(payload)
        return data

    def heartbeat(self):
        """
        Send a simple HEART_BEAT command to device.
        """
        # open device, send request, then close connection
        payload = self.generate_payload(tinytuya.HEART_BEAT)
        data = self._send_receive(payload,0)
        return data

    def set_value(self, index, value):
        """
        Set int value of any index.
        Args:
            index(int): index to set
            value(int): new value for the index
        """
        # open device, send request, then close connection
        if isinstance(index, int):
            index = str(index)  # index and payload is a string

        payload = self.generate_payload(tinytuya.CONTROL, {
            index: value})

        data = self._send_receive(payload)

        return data

def main():
    debug = True
    while True:
        try:
            print(roborock.status())
        except DeviceException as e:
            logging.exception(e)
        except Exception as e:
            logging.exception(e)
            roborock.close()
            break
        time.sleep(5)
    roborock.close()

if __name__ == '__main__':
    main()
