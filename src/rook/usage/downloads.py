import csv
import ipaddress
import logging
import re
import subprocess  # noqa: S404
from datetime import datetime
from functools import lru_cache
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


@lru_cache(maxsize=4096)
def dot2longip(ip):
    """Convert an IPv4 address to an IP number."""
    try:
        return int(ipaddress.IPv4Address(ip))
    except ipaddress.AddressValueError:
        LOGGER.debug(f"Could not convert IP address to an IP number: {ip}. Skipping...")
        return 0


@lru_cache(maxsize=4096)
def parse_record_time(value):
    """Reuse repeated log timestamps with a bounded cache."""
    return datetime.strptime(value, "%d/%b/%Y:%H:%M:%S")


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
        record_time = parse_record_time(tokens[3].lstrip("["))
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
        search_pattern = rf"GET {self.output_path}/.*/.*\.nc"
        request_pattern = re.compile(rf"{self.output_path}/.*/.*\.nc")
        time_start = pd.Timestamp(time_start) if time_start else None
        time_end = pd.Timestamp(time_end) if time_end else None
        fname = Path(outdir).joinpath("downloads.csv").as_posix()
        writer = None

        # Stream one file at a time: neither grep output nor parsed records
        # should accumulate in memory as the log history grows.
        with Path(fname).open("w", newline="") as output:
            for log_file in log_files:
                checkpoint = output.tell()
                previous_writer = writer
                with subprocess.Popen(  # noqa: S603
                    ["zgrep", search_pattern, log_file],  # noqa: S607
                    stdout=subprocess.PIPE,
                    text=True,
                ) as process:
                    try:
                        for line in process.stdout:
                            try:
                                record = parse_record(line)
                            except NotFoundError:
                                continue
                            if writer is None:
                                writer = csv.DictWriter(
                                    output,
                                    fieldnames=record.keys(),
                                    lineterminator="\n",
                                )
                                writer.writeheader()
                            if not request_pattern.search(record["request"]):
                                continue
                            if (
                                time_start is not None
                                and record["datetime"] < time_start
                            ):
                                continue
                            if time_end is not None and record["datetime"] > time_end:
                                continue
                            writer.writerow(record)
                    except BaseException:
                        process.kill()
                        raise
                # Exit 1 means no matches. Discard partial output on errors,
                # as subprocess.run(check=True) did before streaming.
                if process.returncode not in (0, 1):
                    output.seek(checkpoint)
                    output.truncate()
                    writer = previous_writer
                    LOGGER.error(
                        "Failed to process log file %s: zgrep exited with %s",
                        log_file,
                        process.returncode,
                    )

        if writer is None:
            raise NotFoundError("Could not find any records")
        return fname
