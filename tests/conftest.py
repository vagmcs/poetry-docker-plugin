# Standard Library
from pathlib import Path

# Dependencies
import pytest


@pytest.fixture
def dist_directory() -> str:
    path = Path(__file__).resolve()
    while not (path / ".git").exists() and path != path.parent:
        path = path.parent
    return (path / "dist").absolute().as_posix()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if exitstatus == 5:
        session.exitstatus = 0
