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

## Why should you use this over database resources?

### Partitioned assets

If you have a partitioned asset, then when you use it in a downstream asset,
it will need to be filtered for the partition we are running for (via the
partition mapping). The IO manager already handles this using table slice
functionality.

e.g. so if you have a date partitioned asset `my_asset`, when you create a SQL
query: `SELECT * FROM {{ my_asset }}`  in a downstream asset, we get the
partition selection for free. The `load_input` methods can render this into
`SELECT * FROM (SELECT * FROM my_asset WHERE partition_expr >= ... AND partition_expr < ...)`,
whereas we'd have to do this manually using the resources.

### Standardised features and metadata

When you use any IO manager in dagster, dagster truncates the table for you,
before inserting the records. Using database resources, you would
have to make all of these database calls yourself.

``` py

@dg.asset(deps=[my_asset_upstream])
def my_asset_downstream(duckdb: DuckDbResource):
    my_asset_downstream_query = "SELECT *, True AS new_col FROM my_asset_upstream"
    duckdb.sql("DELETE FROM my_asset_downstream")
    duckdb.sql(f"INSERT INTO my_asset_downstream ({my_asset_downstream_query})")
```

vs.

``` py
@dg.asset()
def my_asset_downstream(my_asset_upstream: SqlQuery):
    return SqlQuery("SELECT *, True AS new_col FROM {{ my_asset_upstream }}", my_asset_upstream=my_asset_upstream)
```

You also get the opportunity to add features to your IO manager, such
as adding useful metadata, primary key validation, etc. that apply to every asset
without having to call manually within asset code in each asset.

Therefore, tt allows the continued separation of IO code and business logic which is such
a great feature of dagster.

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
