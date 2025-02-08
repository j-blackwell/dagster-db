import dagster as dg
from duckdb import DuckDBPyConnection
from dagster_db.query.sql_query import SqlQuery


def get_sample_md(obj: SqlQuery, connection: DuckDBPyConnection) -> str:
    ...

def get_table_schema(obj: SqlQuery, connection: DuckDBPyConnection) -> dg.TableSchema:
    ...

def get_rows(obj: SqlQuery, connection: DuckDBPyConnection) -> int:
    ...

def glimpse(obj: SqlQuery, connection: DuckDBPyConnection) -> str:
    ...
