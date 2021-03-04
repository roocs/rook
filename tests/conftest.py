import os
import pytest


from tests.common import write_roocs_cfg, MINI_ESGF_CACHE_DIR

write_roocs_cfg()

TEST_DATA_REPO_URL = "https://github.com/roocs/mini-esgf-data"


@pytest.fixture
def fake_inv():
    os.environ["ROOK_FAKE_INVENTORY"] = "1"


@pytest.fixture
def load_test_data():
    """
    This fixture ensures that the required test data repository
    has been cloned to the cache directory within the home directory.
    """
    from git import Repo

    branch = "master"
    target = os.path.join(MINI_ESGF_CACHE_DIR, branch)

    if not os.path.isdir(MINI_ESGF_CACHE_DIR):
        os.makedirs(MINI_ESGF_CACHE_DIR)

    if not os.path.isdir(target):
        repo = Repo.clone_from(TEST_DATA_REPO_URL, target)
        repo.git.checkout(branch)

    elif os.environ.get("ROOCS_AUTO_UPDATE_TEST_DATA", "true").lower() != "false":
        repo = Repo(target)
        repo.git.checkout(branch)
        repo.remotes[0].pull()
