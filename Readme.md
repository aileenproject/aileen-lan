# Aileen sensoring for IP adresses in an Local Area Network

This code will, in conjunction with an Aileen core box,
scan the local area network (LAN) for IP addresses.


## Setup

0. Make a virtual env (we used Python 3.6) and activate it
1. Get aileen-core and aileen-lan code, and install dependencies
   * `git clone git@github.com:aileenproject/aileen-core.git`
   * `cd aileen-core`
   * `git clone git@github.com:aileenproject/aileen-lan.git`
   * `pip install -r aileen-lan/requirements.txt`
   * `python setup.py develop` 
   * `cd aileen`
   * `python manage.py migrate`
   * `python manage.py fill_settings --server-url dummy.server --upload-token "sometoken"`
2. Make sure aileen-core knows and can find aileen-lan's sensor module
    * `export AILEEN_ACTIVATE_VENV_CMD="source activate my-aileen-venv"`
    * `export PYTHONPATH=/full/path/to/aileen-lan` (Note: this one really needs to happen on the shell before you run aileen-lan, i.e. not in .env)
    * `export AILEEN_SENSOR_MODULE=sensor`
3. Further configuration of aileen-lan
   You can set/export the following env variables:
    * AILEEN_INTERNET_CONNECTION_AVAILABLE (defaults to "yes" - if you're in an offline setting, this keeps Aileen from trying to upload)
    * AILEEN_LAN_INTERVAL_IN_SECONDS (defaults to 300)
    * AILEEN_LAN_SUBNET_MASK (defaults to "192.168.1.0/24")
    * AILEEN_LAN_TIMEZONE (defaults to "UTC")
   See aileen-core/Readme file for more.
4. Start/stop the box:
  * `python manage.py run_box`
  * `python manage.py stop_box`

Aileen-lan should now start filling the local database.`tmux attach` if you're interested to peek inside if everything is working.
(Ctrl-b-<tab-index> switches tmux tabs, Ctrl-b-d detaches from the session)


## Troubleshooting

You can test directly in a python console if your aileen-lan sensor is findable and works.
You should have included the aileen-lan directory in the PYTHONPATH and set the SENSOR_MODULE env variable (see step 3 above).

Then open a python console and do this:

    import importlib
    sensor = importlib.import_module("sensor") 
    sensor.start_sensing("/tmp/aileen-lan")



## Server setup

TODO

`python manage.py create_box --id 7e84fca5-e3d6-4721-a39a-4d1781a23124 --name classsroom --description "Counting connected learning computers"`
