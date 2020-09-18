# pyroborock

See https://github.com/89jd/roborock_comms for details on how I go to this point.

Using the keys from roborock app, it is possible to communicate with the roborock without needing to use the Xiamoi Miio app.

It creates a new class overriding the python-miio vacuum class, but uses the tuya-ipc library to communicate
