from typing import Optional, Sequence, Type
import dagster as dg
from dagster_duckdb.io_manager import DuckDBIOManager, DuckDbClient

from io_managers.custom_db_io_manager import CustomDbIOManager
from type_handlers.custom_type_handler import CustomDbTypeHandler


def build_custom_duckdb_io_manager(
    type_handlers: Sequence[CustomDbTypeHandler],
    default_load_type: Optional[Type] = None,
    io_manager_name: str = "DuckDbIoManager"
) -> dg.IOManagerDefinition:
    @dg.io_manager(config_schema=DuckDBIOManager.to_config_schema())
    def duckdb_io_manager(init_context):
        return CustomDbIOManager(
            type_handlers=type_handlers,
            db_client=DuckDbClient(),
            io_manager_name=io_manager_name,
            database=init_context.resource_config["database"],
            schema=init_context.resource_config.get("schema"),
            default_load_type=default_load_type,
        )

    return duckdb_io_manager
