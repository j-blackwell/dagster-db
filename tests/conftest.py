from typing import Any
import pytest

from dagster_db import build_custom_duckdb_io_manager


@pytest.fixture(scope="module")
def resources() -> dict[str, Any]:
    return {
        "io_manager": build_custom_duckdb_io_manager().configured(
            {"database": "./.tests/database.duckdb"}
        ),
    }
