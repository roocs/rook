import pandas as pd
from rook.usage import Downloads

from .common import resource_file


def test_usage_downloads(tmpdir):
    collector = Downloads()
    stats_csv = collector.parse(
        log_files=[resource_file("access.log.txt")], outdir=tmpdir
    )
    print(stats_csv)
    df = pd.read_csv(stats_csv)
    assert len(df) == 4
