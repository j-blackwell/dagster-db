# dagster-db

Dagster IO managers and type handlers for databases.
Wraps the standard IO managers with useful functions that can be scpecific to
each type handler, and provides better metadata out of the box.

- Apply custom generic transformations to ensure all outputs comply with database.
- Apply custom validation checks before deleting from / writing to the database.
- Add custom metadata.

Use `polars`, `pandas` or execute a jinja-templated `SQL` query on the database
with the custom `SqlQuery` class which builds `dagster`s powerful table slice
logic into an io-manager ready framework.

Use `TypeHandlers` out of the box, or extend to implement custom behaviours.

## duckdb

### Installation

```bash
uv add dagster-db[duckdb]
```

### Definition

```py
import dagster as dg
from dagster_db import build_custom_duckdb_io_manager
custom_io_manager = build_custom_duckdb_io_manager().configured({"database": "./.tmp/database.duckdb"})

defs = dg.Definitions(
    ...,
    resources={"io_manager": custom_io_manager},
)
```

### Usage

```py
import dagster as dg
import polars as pl
from dagster_db import SqlQuery

@dg.asset
def my_asset(context: dg.AssetExecutionContext) -> pl.DataFrame:
    return pl.DataFrame({"a": [1, 2, 3]})

@dg.asset
def my_asset_downstream(
    context: dg.AssetExecutionContext,
    my_asset: SqlQuery,
) -> SqlQuery:
    return SqlQuery("SELECT *, a+1 AS b FROM {{ my_asset }}", my_asset)
```
