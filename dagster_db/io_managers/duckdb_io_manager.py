from typing import Optional, Sequence, Type
import dagster as dg
from dagster_duckdb.io_manager import DuckDBIOManager, DuckDbClient

from dagster_db.io_managers.custom_db_io_manager import build_custom_db_io_manager
from dagster_db.type_handlers.custom_type_handler import CustomDbTypeHandler
from dagster_db.type_handlers.duckdb_pandas import DuckDbPandasTypeHandler
from dagster_db.type_handlers.duckdb_polars import DuckDbPolarsTypeHandler
from dagster_db.type_handlers.duckdb_sql_query import DuckDbSqlQueryTypeHandler


def build_custom_duckdb_io_manager(
    type_handlers: Sequence[CustomDbTypeHandler] = [DuckDbPandasTypeHandler, DuckDbPolarsTypeHandler, DuckDbSqlQueryTypeHandler,],
    default_load_type: Optional[Type] = None,
    io_manager_name: str = "DuckDbIoManager"
) -> dg.IOManagerDefinition:
    return build_custom_db_io_manager(io_manager_base=DuckDBIOManager, db_client=DuckDbClient(), type_handlers=type_handlers, default_load_type=default_load_type, io_manager_name=io_manager_name,)
