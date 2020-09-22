import base64
import json
import os
import sys
import asyncio
import threading
import logging

import tuyapipc
from tuyapipc import TuyaNodeWrapper

from miio.vacuum import Vacuum
from miio.exceptions import DeviceError, DeviceException, RecoverableError

from typing import Any, Dict, List

from Crypto.Cipher import AES
from subprocess import Popen, PIPE
import time

#Message keys
DISCONNECTED = 'disconnected'
CONNECTED = 'connected'
READY = 'ready'
RESPONSE = 'response'

TYPE = 'type'

debug = False

class TuyaProtocol:
    def __init__(self, ip, token, device_id, js_dir='./', debug=False):
        self.__id = 9999
        
        self.ip = ip 
        self.token = token
        self.device_id = device_id

        self.tuya_node_wrapper = TuyaNodeWrapper(message_received_callback=self._on_tuya_message_received, js_location=js_dir, debug=debug)
        self.tuya_node_wrapper.start()
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
        if message[TYPE] == CONNECTED:
            self.is_connected_to_roborock = True
        if message[TYPE] == READY:
            self.is_ready_for_comms = True
        if message[TYPE] == DISCONNECTED:
            self.is_connected_to_roborock = False
            self.is_ready_for_comms = False
        elif message[TYPE] == RESPONSE:
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
        is_ready = self.is_connected_to_roborock and self.is_ready_for_comms
        
        if not is_ready:
            self.tuya_node_wrapper.connect_device(self.ip, self.device_id, self.token)

        time_waiting = 0
        while not self.is_connected_to_roborock or not self.is_ready_for_comms:
            if time_waiting > 10:
                raise DeviceException('Timed out waiting for response')
            time.sleep(0.2)
            time_waiting += 0.2
        
        req = self._create_request(command, parameters, extra_parameters)
        req_id = req['id']
        req = json.dumps(req)
        tuya_req = base64.b64encode(req.replace(' ', '').encode('utf-8')).decode('utf-8')
        
        self.tuya_node_wrapper.set_dps(101, tuya_req)

        time_waiting = 0
        while req_id not in self.responses:
            del self.responses[req_id]
            if time_waiting > 10:
                raise DeviceException('No response received')
            time.sleep(0.2)
            time_waiting += 0.2
        
        try:
            return json.loads(self.responses[req_id].decode('utf8'))['result']
        except Exception as e:
            raise DeviceException('Error decoding response') from e


    def close(self):
        self.tuya_node_wrapper.disconnect()

class Roborock(Vacuum):
    """Main class representing the vacuum."""

    def __init__(
        self, ip: str, token: str, device_id: str, js_dir: str = './', debug: int = 0
    ) -> None:
        super().__init__(ip, token, debug=debug)
        print(debug != 0)
        self._protocol = TuyaProtocol(ip, token, device_id, js_dir=js_dir, debug=debug != 0)

    def close(self):
        self._protocol.close()

def main():
    debug = True
    tuyapipc.init('./')
    
    roborock = Roborock(sys.argv[1], sys.argv[3], sys.argv[2], debug=1)
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