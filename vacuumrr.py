import base64
import json
import os
import sys
import asyncio
import threading

import tuyapipc
from tuyapipc import TuyaNodeWrapper

from miio.vacuum import Vacuum

from typing import Any, Dict, List

from Crypto.Cipher import AES
from subprocess import Popen, PIPE
import time


class TuyaProtocol:
    def __init__(self, ip, token, device_id):
        self.__id = 9999
        self.tuya_node_wrapper = TuyaNodeWrapper(message_received_callback=self._on_tuya_message_received)
        self.tuya_node_wrapper.start()
        self.tuya_node_wrapper.connect_device(ip, device_id, token)
        self.responses = {}
        self.is_connected_to_roborock = False
        self.is_ready_for_comms = False

    def _ob_exists_recursive(self, keys, ob, i=0):
        if keys[i] in ob:
            if i == len(keys) - 1:
                return True
            else:
                return self._ob_exists_recursive(keys, ob[keys[i]], i+1)
        else:
            return False

    def _on_tuya_message_received(self, message):
        if message['type'] == 'connected':
            self.is_connected_to_roborock = True
        if message['type'] == 'ready':
            self.is_ready_for_comms = True
        elif message['type'] == 'response':
            if self._ob_exists_recursive(['data', 'dps', '102'], message):
                resp = message['data']['dps']['102']
                if resp:
                    decoded = base64.b64decode(resp.encode('utf-8'))
                    decoded_ob = json.loads(decoded)
                    if 'id' in decoded_ob:
                        self.responses[decoded_ob['id']] = decoded

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
        time_waiting = 0
        while not self.is_connected_to_roborock or not self.is_ready_for_comms:
            if time_waiting > 10:
                return None
            time.sleep(0.2)
            time_waiting += 0.2
        
        req = self._create_request(command, parameters, extra_parameters)
        req_id = req['id']
        req = json.dumps(req)
        tuya_req = base64.b64encode(req.replace(' ', '').encode('utf-8')).decode('utf-8')
        
        self.tuya_node_wrapper.set_dps(101, tuya_req)

        time_waiting = 0
        while req_id not in self.responses:
            if time_waiting > 10:
                return None
            time.sleep(0.2)
            time_waiting += 0.2
        
        return json.loads(self.responses[req_id].decode('utf8'))['result']

    def close(self):
        self.tuya_node_wrapper.disconnect()

class Roborock(Vacuum):
    """Main class representing the vacuum."""

    def __init__(
        self, ip: str, token: str, device_id: str, debug: int = 0
    ) -> None:
        super().__init__(ip, token, debug=debug)
        self._protocol = TuyaProtocol(ip, token, device_id)

    def close(self):
        self._protocol.close()

def main():
    tuyapipc.init('./')
    roborock = Roborock(sys.argv[1], sys.argv[3], sys.argv[2])
    print(roborock.status())
    roborock.close()

if __name__ == '__main__':
    main()