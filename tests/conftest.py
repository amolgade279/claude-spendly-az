import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield tmp_path


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    original_cwd = os.getcwd()
    tmp_dir = tmp_path_factory.mktemp("spendly_app")
    os.chdir(tmp_dir)

    try:
        from app import app as flask_app
    except Exception:
        os.chdir(original_cwd)
        raise

    flask_app.config.update(TESTING=True)

    yield flask_app

    os.chdir(original_cwd)
