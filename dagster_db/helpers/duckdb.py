import pandas as pd
import polars as pl
from duckdb import DuckDBPyConnection
from dagster_db.query.sql_query import SqlQuery
from dagster import get_dagster_logger

from typing import Optional, Type, TypeVar

T = TypeVar("T", list, tuple, pd.DataFrame, pl.DataFrame, DuckDBPyConnection)


def execute_duckdb(
    query: SqlQuery,
    connection: DuckDBPyConnection,
    obj: Optional[pl.DataFrame | pd.DataFrame] = None,
    return_type: Type[T] = DuckDBPyConnection,
) -> T:
    log = get_dagster_logger()
    query_rendered = query.render()
    log.debug(f"Running query:\n{query_rendered}")
    result = connection.execute(query_rendered)
    if return_type is list:
        return_value = result.fetchall()
    elif return_type is tuple:
        return_value = result.fetchone()
    elif return_type is pd.DataFrame:
        return_value = result.df()
    elif return_type is pl.DataFrame:
        return_value = result.pl()
    elif return_type is DuckDBPyConnection:
        return_value = result
    else:
        raise TypeError(f"Unsupported {return_type=}")

    return return_value  # type: ignore
