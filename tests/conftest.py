import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield tmp_path
