import ipaddress
import logging
import subprocess  # noqa: S404
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
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
    MIN_EXPECTED_TOKENS = 12  # noqa: N806

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
        log_files = sorted(Path(self.http_log_path).glob("access.log*"))
        return self.parse(log_files, time_start, time_end, outdir)

    def parse(self, log_files, time_start=None, time_end=None, outdir=None):
        def process_file(log_file):
            records = []
            try:
                # FIXME: This is very insecure, as it allows for command injection
                # Use zgrep to pre-filter logs based on the output path
                p = subprocess.run(  # noqa: S603
                    ["zgrep", search_pattern, log_file],  # noqa: S607
                    stdout=subprocess.PIPE,
                    text=True,
                    check=True,
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
            return records

        search_pattern = rf"GET {self.output_path}/.*/.*\.nc"
        all_records = []

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(process_file, log_file) for log_file in log_files
            ]
            for future in futures:
                all_records.extend(future.result())

        if not all_records:
            raise NotFoundError("Could not find any records")

        df = pd.DataFrame(all_records)
        df = df[
            df["request"].str.contains(rf"{self.output_path}/.*/.*\.nc", regex=True)
        ]

        if time_start:
            df = df[df["datetime"] >= time_start]
        if time_end:
            df = df[df["datetime"] <= time_end]

        fname = Path(outdir).joinpath("downloads.csv").as_posix()
        df.to_csv(fname, index=False)
        return fname
