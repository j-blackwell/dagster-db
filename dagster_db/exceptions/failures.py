import dagster as dg
from typing import Any
import polars as pl
import pandas as pd

from dagster_db.helpers import polars as h_polars
from dagster_db.helpers import pandas as h_pandas
from dagster_db.helpers import sql_query as h_sql
from dagster_db.query.sql_query import SqlQuery


def obj_to_md(obj: Any, connection: Any = None):
    if isinstance(obj, pl.DataFrame):
        return h_polars.get_sample_md(obj)
    elif isinstance(obj, pd.DataFrame):
        return h_pandas.get_sample_md(obj)
    elif isinstance(obj, SqlQuery):
        return h_sql.get_sample_md(obj, connection)
    else:
        raise TypeError(f"`obj` is of unsupported type: {type(obj)}")


class DbTablesIncompatibleFailure(dg.Failure):
    def __init__(self, tables: dict[str, Any], connection: Any = None):
        table_names = ", ".join(tables.keys())
        metadata = {k: obj_to_md(v, connection) for k, v in tables.items()}
        raise dg.Failure(
            description=f"[{table_names}] are not compatible.",
            metadata=metadata,
        )
