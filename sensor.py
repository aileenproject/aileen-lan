import subprocess
import sys
import os
import re
import shlex
from datetime import datetime
import pytz
import time
import logging

import dateutil.parser as dtparser
import pandas as pd

"""
Tool to sense all active IP addresses in a network.
This implements the Aileen-Core API, so data can be collected, aggregated and uploaded.

You can set the following env variables:
    * AILEEN_LAN_SUBNET_MASK (this one is important, see below for help - it defaults to "192.168.1.0/24")
    * AILEEN_LAN_INTERVAL_IN_SECONDS (defaults to 300)
    * AILEEN_LAN_TIMEZONE (defaults to "UTC")

You can use `ifconfig` or `ip addr show` to find the subnet mask
(see https://www.tecmint.com/find-live-hosts-ip-addresses-on-linux-network/).
Note that you are partly responsible how long each scan takes, as you choose the subnet mask.
As an example, I just ran nmap and it scanned 256 IP addresses. 25 hosts were up, and the scan took 12.12 seconds.

With a local Aileen Core installation, setting this module as the sensor and starting
to run would be:

    export AILEEN_SENSOR_MODULE=sensor
    export AILEEN_ACTIVATE_VENV_CMD="source activate my-eventual-aileen-venv"
    export PYTHONPATH=/path/to/aileen-lan
    python manage.py start_box

(For further configuration, consult Aileen Core's documentation, i.e. aileen/settings.py)
"""

IP_SCAN_CMD = "nmap -sn %s"
LBL = "[Aileen-LAN]"
TMP_FILE_NAME = "aileen-lan-nmap.out"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def check_preconditions():
    """
    Check any preconditions this sensor needs and raise if you're not happy.
    """
    output = subprocess.check_output(["which", "nmap"])
    if "not found" in output.decode("utf-8"):
        logger.error("%s ERROR: nmap seems not to be installed or on the path!" % LBL)
        sys.exit(2)
    logger.debug("%s I am fine with startibng the LAN mapping :)")


def get_subnet_mask():
    return os.environ.get("AILEEN_LAN_SUBNET_MASK", default="192.168.1.0/24")


def sleep_until_interval_is_complete(start_time, interval_in_seconds):
    """ take a break, so in all we will have spent x seconds, incl. runtime"""
    run_time = time.time() - start_time
    rest_interval_in_seconds = interval_in_seconds - (run_time % interval_in_seconds)
    logger.info("Sleeping for %.2f seconds ..." % rest_interval_in_seconds)
    time.sleep(rest_interval_in_seconds)


def start_sensing(tmp_path: str = None):
    """
    This starts running the sensor regularly. Aileen calls this once and keeps it alive in a tmux session.
    """
    interval = int(os.environ.get("AILEEN_LAN_INTERVAL_IN_SECONDS", default=5 * 60))
    start_time = time.time()
    while True:
        scan_ips(tmp_path)
        logger.info(
            "%s Sleeping until %d seconds have passed since last ip scan  ..."
            % (LBL, interval)
        )
        sleep_until_interval_is_complete(start_time, interval)


def scan_ips(tmp_path: str = None):
    """
    Read nmap output and store it for later reading.
    """
    if tmp_path is None:
        tmp_path = "/tmp"
    args = shlex.split(IP_SCAN_CMD % get_subnet_mask())
    logger.debug(f"{LBL} Calling nmap on subnet mask %s..." % get_subnet_mask())
    output = subprocess.check_output(args)
    logger.debug(f"{LBL} Producing nmap output ...")
    with open("%s/%s" % (tmp_path, TMP_FILE_NAME), "w") as nmap_output:
        nmap_output.write(output.decode("utf-8"))


def find_ip(s: str) -> str:
    """Find the first IP address in the string and return it"""
    regex = r'(?:\d{1,3}\.)+(?:\d{1,3})'
    ip_pattern = re.compile(regex)
    ips = re.findall(ip_pattern, s)
    if len(ips) > 0:
        return ips[0]
    else:
        return ""


def get_latest_reading_as_df(tmp_path: str = None):
    """
    Return the latest reading in the dataframe format required by Aileen-core.
    """
    logger.debug(f"{LBL} Reading latest nmap output ...")
    if tmp_path is None:
        tmp_path = "/tmp"
    empty_df = pd.DataFrame(columns=["observable_id", "time_seen", "value"])
    sensor_output = ""
    result = []
    with open("/".join((tmp_path.rstrip("/"), TMP_FILE_NAME)), "r") as nmap_output:
        sensor_output = nmap_output.readlines()

    if len(sensor_output) == 0:
        logger.warning("%s WARNING: Got no output from nmap!" % LBL)
        return empty_df

    # get the date from the namp output (usually first or second line)
    scan_time: datetime = None
    lan_tz = pytz.timezone(os.environ.get("AILEEN_LAN_TIMEZONE", "UTC"))
    for line in sensor_output:
        if line.startswith("Starting Nmap"):
            try:
                scan_time = dtparser.parse(line.split(" at ")[1]).astimezone(lan_tz)
            except:
                pass
            break
    if scan_time is None:
        print(
            "%s WARNING: Could not find scan time in output from nmap, using now!" % LBL
        )
        now = datetime.now().astimezone(lan_tz)

    current_ip = None
    for line in sensor_output:
        if not line.startswith("Nmap scan report") and not line.startswith("Host is"):
            continue
        if "scan report for" in line:
            current_ip = find_ip(line.split("for ")[1].strip())
        elif current_ip is not None:
            if "Host is up" in line:
                result.append(
                    {
                        "observable_id": current_ip,
                        "time_seen": scan_time,
                        "value": 1,
                        "observations": {"source": "nmap"},
                    }
                )
        else:
            continue
    df = pd.DataFrame(result)
    if df.index.size == 0:
        return empty_df
    logger.info(
        f"{LBL} At {scan_time}, nmap found {df.index.size} connected computers in {get_subnet_mask()}."
    )
    return df
