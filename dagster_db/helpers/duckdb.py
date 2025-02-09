import pandas as pd
import polars as pl
from duckdb import DuckDBPyConnection
from dagster_db.query.sql_query import SqlQuery

from typing import Type, TypeVar

T = TypeVar("T", list, tuple, pd.DataFrame, pl.DataFrame, DuckDBPyConnection)

def execute_duckdb(query: SqlQuery, connection: DuckDBPyConnection, return_type: Type[T] = DuckDBPyConnection) -> T:
    result = connection.execute(query.render())
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

    return return_value # type: ignore

