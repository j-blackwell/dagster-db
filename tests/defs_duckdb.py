import uuid
import dagster as dg
import pandas as pd
from dagster_db import build_custom_duckdb_io_manager


@dg.asset
def my_asset():
    return pd.DataFrame(
        {str(abs(hash(str(i)))): [1, 2, 3] for i in range(10)},
    )


defs = dg.Definitions(
    assets=[my_asset],
    resources={
        "io_manager": build_custom_duckdb_io_manager().configured(
            {"database": "./.tests/database.duckdb"}
        ),
    },
)
