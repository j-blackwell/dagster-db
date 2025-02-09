import pandas as pd
import polars as pl
from duckdb import DuckDBPyConnection
from dagster_db.query.sql_query import SqlQuery

from typing import Type, TypeVar

T = TypeVar("T", list, tuple, pd.DataFrame, pl.DataFrame, DuckDBPyConnection)

def table_slice_to_schema_table(table_slice, sep="."):
    return table_slice.schema + sep + table_slice.table

def execute_duckdb(query: SqlQuery, connection: DuckDBPyConnection, return_type: Type[T] = DuckDBPyConnection) -> T:
    result = connection.execute(query.render())
    if return_type is list:
        return result.fetchall() #type: ignore
    if return_type is tuple:
        return result.fetchone() #type: ignore
    if return_type is pd.DataFrame:
        return result.df() #type: ignore
    if return_type is pl.DataFrame:
        return result.pl() #type: ignore
    if return_type is DuckDBPyConnection:
        return result #type: ignore

    raise TypeError(f"Unsupported {return_type=}")
