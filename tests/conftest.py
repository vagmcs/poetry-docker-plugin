from pathlib import Path

import pytest


@pytest.fixture
def dist_directory() -> str:
    path = Path(__file__).resolve()
    while not (path / ".git").exists() and path != path.parent:
        path = path.parent
    return (path / "dist").absolute().as_posix()
