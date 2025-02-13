from typing import Optional
import pandas as pd
import polars as pl
import dagster as dg
from duckdb import DuckDBPyConnection
from dagster_db.helpers.duckdb import execute_duckdb
from dagster_db.query.sql_query import SqlExpr, SqlQuery


def get_sample_md(
    obj: SqlQuery,
    connection: DuckDBPyConnection,
    n: int = 10,
    order_by="RANDOM()",
) -> Optional[str]:
    order_by = SqlExpr(order_by)
    sample_query = SqlQuery(
        "SELECT * FROM {{ obj }} ORDER BY {{ order_by }} LIMIT {{ n }}",
        obj=obj,
        order_by=order_by,
        n=n,
    )
    df = execute_duckdb(sample_query, connection, return_type=pd.DataFrame)
    return df.to_markdown()


def get_table_schema(obj: SqlQuery, connection: DuckDBPyConnection) -> dg.TableSchema:
    sample_query = SqlQuery("SELECT * FROM {{ obj }} LIMIT 0", obj=obj)
    result = execute_duckdb(sample_query, connection, return_type=DuckDBPyConnection)
    description = result.description
    assert description is not None
    return dg.TableSchema(
        columns=[dg.TableColumn(name=field[0], type=field[1]) for field in description]
    )


def get_rows(obj: SqlQuery, connection: DuckDBPyConnection) -> int:
    count_query = SqlQuery("SELECT COUNT(*) as count FROM {{ obj }}", obj=obj)
    result = execute_duckdb(count_query, connection, return_type=tuple)
    return result[0]


def glimpse(obj: SqlQuery, connection: DuckDBPyConnection, n: int = 10) -> str:
    sample_query = SqlQuery("SELECT * FROM {{ obj }} LIMIT {{ n }}", obj=obj, n=n)
    df = execute_duckdb(sample_query, connection, return_type=pl.DataFrame)
    return df.glimpse(return_as_string=True)
