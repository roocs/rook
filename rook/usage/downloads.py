import subprocess
from datetime import datetime
import gzip
import os
import glob
from urllib.parse import urlparse
import ipaddress
import pandas as pd

from pywps import configuration as config

from .base import Usage

import logging

LOGGER = logging.getLogger()


class NotFoundError(Exception):
    """Value not found Exception"""

    pass


class AddressValueError(Exception):
    """IP address value error"""

    pass


def dot2longip(ip):
    """Converts an IPv4 address to an IP number"""

    ip_number = 0

    try:
        parsed_ip = ipaddress.IPv4Address(ip)
        ip_number = int(parsed_ip)
    except (AddressValueError, ipaddress.AddressValueError):
        ip_number = 0
        msg = (
            "Could not convert this IP address to an IP number: {}." "Skipping..."
        ).format(ip)
        LOGGER.debug(msg)

    return ip_number


def parse_record(line):
    """
    Parse a log record.

    :param line: access log record line

    :returns: dict with log record
    """
    # result record
    record = dict()
    # raw line / record
    _line = line.strip()
    # remote host (IP)
    record["remote_host_ip"] = None
    # converted remote host IP address to IP number
    record["ip_number"] = None
    # datetime.datetime object of request
    record["datetime"] = None
    # timezone request
    record["timezone"] = None
    # type of HTTP request (GET, POST, etc.)
    record["request_type"] = None
    # HTTP request
    record["request"] = None
    # protocol and version of request
    record["protocol"] = None
    # HTTP response status code
    record["status_code"] = 0
    # size of HTTP response
    record["size"] = 0
    # Referer
    record["referer"] = None
    # User-Agent
    record["user_agent"] = None

    LOGGER.debug("Parsing log record")
    tokens = _line.split()

    if len(tokens) < 12:
        msg = "Line does not contain expected apache record format"
        LOGGER.warning(msg)
        raise NotFoundError(msg)

    # validate IP address
    record["ip_number"] = dot2longip(tokens[0])
    if record["ip_number"] != 0:
        record["remote_host_ip"] = tokens[0]

    try:
        record["datetime"] = datetime.strptime(
            tokens[3].lstrip("["), "%d/%b/%Y:%H:%M:%S"
        )
    except ValueError:
        msg = (
            "Datetime token ({}) that does not match the expected " "datetime format"
        ).format(tokens[3].lstrip("["))
        LOGGER.warning(msg)
        raise NotFoundError(msg)

    record["timezone"] = tokens[4].rstrip("]")
    record["request_type"] = tokens[5].lstrip('"')
    record["request"] = tokens[6]
    record["protocol"] = tokens[7].rstrip('"')

    try:
        record["status_code"] = int(tokens[8])
        if tokens[9] != "-":  # ignore size values that are "-"
            record["size"] = int(tokens[9])
    except ValueError:
        msg = (
            "Status code ({}) or size ({}) are invalid literals for " "int type"
        ).format(tokens[8], tokens[9])
        LOGGER.warning(msg)
        raise NotFoundError(msg)

    record["referer"] = tokens[10].replace('"', "")
    record["user_agent"] = " ".join(tokens[11:]).lstrip('"').rstrip('"')
    return record


class Downloads(Usage):
    def __init__(self):
        self.output_path = urlparse(config.get_config_value("server", "outputurl")).path
        self.http_log_path = config.get_config_value("logging", "http_log_path")

    def collect(self, time_start=None, time_end=None, outdir=None):
        log_files = sorted(glob.glob(os.path.join(self.http_log_path, "access.log*")))
        return self.parse(log_files, time_start, time_end, outdir)

    def parse(self, log_files, time_start=None, time_end=None, outdir=None):
        records = []
        for f in log_files:
            p = subprocess.run(["zgrep", self.output_path, f], stdout=subprocess.PIPE)
            lines = p.stdout.split(b"\n")
            for line in lines:
                try:
                    record = parse_record(line.decode())
                except NotFoundError:
                    continue
                if not record["request"].startswith(self.output_path):
                    continue
                records.append(record)
        if not records:
            raise NotFoundError("could not find any records")
        df = pd.DataFrame(records)
        df = df.loc[
            df["request"].str.contains(rf"{self.output_path}/.*/.*\.nc", regex=True)
        ]  # noqa
        # df['datetime'] = pd.to_datetime(df['datetime'])
        if time_start:
            df = df.loc[df["datetime"] >= time_start]
        if time_end:
            df = df.loc[df["datetime"] <= time_end]
        fname = os.path.join(outdir, "downloads.csv")
        df.to_csv(fname, index=False)
        return fname
