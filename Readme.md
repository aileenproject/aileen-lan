# Aileen sensoring for IP adresses in an Local Area Network

This code will, in conjunction with an Aileen core box,
scan the local area network (LAN) for IP addresses.

## Setup the LAN scanning sensor

    0. Include the aileen-lan directory in the PYTHONPATH and set the SENSOR_MODULE env variable
    1. Test if the code works:

        import importlib
        sensor = importlib.import_module("sensor") 
        sensor.read_sensor("/tmp/aileen-lan")

## Setup

0. Make a virtual env and activate it
1. Get aileen-core and install its dependencies
   git clone ... TODO
   python setup.py develop
2. Set at least the env variable SENSOR_MODULE
3. sudo service aileen start
