import os
import glob
import subprocess
from datetime import datetime
import ipaddress
import logging
from urllib.parse import urlparse

import pandas as pd
from pywps import configuration as config

from .base import Usage

LOGGER = logging.getLogger()


class NotFoundError(ValueError):
    """Raised when a log entry is not found or is invalid."""

    pass


class AddressValueError(ValueError):
    """Raised when an IP address cannot be parsed."""

    pass


def dot2longip(ip):
    """Converts an IPv4 address to an IP number."""
    try:
        return int(ipaddress.IPv4Address(ip))
    except ipaddress.AddressValueError:
        LOGGER.debug(f"Could not convert IP address to an IP number: {ip}. Skipping...")
        return 0


def parse_record(line):
    """Parse a log record into a dictionary."""
    tokens = line.strip().split()
    MIN_EXPECTED_TOKENS = 12

    if len(tokens) < MIN_EXPECTED_TOKENS:
        LOGGER.warning("Line does not contain the expected apache record format")
        raise NotFoundError("Invalid log line format")

    ip_number = dot2longip(tokens[0])
    if ip_number == 0:
        raise NotFoundError("Invalid IP address")

    try:
        record_time = datetime.strptime(tokens[3].lstrip("["), "%d/%b/%Y:%H:%M:%S")
    except ValueError:
        LOGGER.warning(f"Invalid datetime format: {tokens[3].lstrip('[')}")
        raise NotFoundError("Invalid datetime format")

    try:
        status_code = int(tokens[8])
        size = int(tokens[9]) if tokens[9] != "-" else 0
    except ValueError:
        LOGGER.warning(f"Invalid status code or size: {tokens[8]}, {tokens[9]}")
        raise NotFoundError("Invalid status code or size")

    return {
        "remote_host_ip": tokens[0],
        "ip_number": ip_number,
        "datetime": record_time,
        "timezone": tokens[4].rstrip("]"),
        "request_type": tokens[5].lstrip('"'),
        "request": tokens[6],
        "protocol": tokens[7].rstrip('"'),
        "status_code": status_code,
        "size": size,
        "referer": tokens[10].replace('"', ""),
        "user_agent": " ".join(tokens[11:]).strip('"'),
    }


class Downloads(Usage):
    def __init__(self):
        self._output_path = urlparse(
            config.get_config_value("server", "outputurl")
        ).path
        self._http_log_path = config.get_config_value("logging", "http_log_path")

    @property
    def output_path(self):
        return self._output_path

    @property
    def http_log_path(self):
        return self._http_log_path

    def collect(self, time_start=None, time_end=None, outdir=None):
        log_files = sorted(glob.glob(os.path.join(self.http_log_path, "access.log*")))
        return self.parse(log_files, time_start, time_end, outdir)

    def parse(self, log_files, time_start=None, time_end=None, outdir=None):
        records = []
        # zgrep "GET /outputs/rook/.*/.*\.nc" /var/log/nginx/access.log-20240801.gz
        search_pattern = (
            rf"GET {self.output_path}/.*/.*\.nc"  # Match request with the output path
        )

        for log_file in log_files:
            try:
                # Use zgrep to pre-filter logs based on the output path
                p = subprocess.run(
                    ["zgrep", search_pattern, log_file],
                    stdout=subprocess.PIPE,
                    text=True,  # Automatically decode stdout to strings
                    check=True,  # Raise CalledProcessError if the command fails
                )
                lines = p.stdout.splitlines()

                for line in lines:
                    try:
                        record = parse_record(line)
                        records.append(record)
                    except NotFoundError:
                        continue
            except subprocess.CalledProcessError as e:
                LOGGER.error(f"Failed to process log file {log_file}: {e}")
                continue

        if not records:
            raise NotFoundError("Could not find any records")

        df = pd.DataFrame(records)
        df = df[
            df["request"].str.contains(rf"{self.output_path}/.*/.*\.nc", regex=True)
        ]

        if time_start:
            df = df[df["datetime"] >= time_start]
        if time_end:
            df = df[df["datetime"] <= time_end]

        fname = os.path.join(outdir, "downloads.csv")
        df.to_csv(fname, index=False)
        return fname
