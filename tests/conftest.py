import os
import pytest

from tests.common import write_roocs_cfg

write_roocs_cfg()


@pytest.fixture
def fake_inv():
    os.environ['ROOK_FAKE_INVENTORY'] = '1'
