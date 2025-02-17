from typing import (
    Optional,
    Sequence,
    Type,
    Any,
    cast,
)
from pathlib import Path
import time

from dagster._core.storage.db_io_manager import DbIOManager, DbClient
import dagster as dg
import dagster._check as check

from dagster_db.type_handlers.custom_type_handler import CustomDbTypeHandler


class CustomDbIOManager(DbIOManager):
    def __init__(
        self,
        *,
        type_handlers: Sequence[CustomDbTypeHandler],
        db_client: DbClient,
        database: str,
        schema: Optional[str] = None,
        io_manager_name: Optional[str] = None,
        default_load_type: Optional[Type] = None,
    ):
        self._handlers_by_type: dict[Optional[type[Any]], CustomDbTypeHandler] = {}  # type: ignore
        self._io_manager_name = io_manager_name or self.__class__.__name__
        for type_handler in type_handlers:
            for handled_type in type_handler.supported_types:
                check.invariant(
                    handled_type not in self._handlers_by_type,
                    f"{self._io_manager_name} provided with two handlers for the same type. "
                    f"Type: '{handled_type}'. Handler classes: '{type(type_handler)}' and "
                    f"'{type(self._handlers_by_type.get(handled_type))}'.",
                )
                self._handlers_by_type[handled_type] = type_handler

        Path(database).parent.mkdir(parents=True, exist_ok=True)

        self._db_client = db_client
        self._database = database
        self._schema = schema
        if (
            default_load_type is None
            and len(type_handlers) == 1
            and len(type_handlers[0].supported_types) == 1
        ):
            self._default_load_type = type_handlers[0].supported_types[0]
        else:
            self._default_load_type = default_load_type

    def handle_output(self, context: dg.OutputContext, obj: object) -> None:
        t0 = time.perf_counter()
        obj_type = type(obj)
        self._check_supported_type(obj_type)
        table_slice = self._get_table_slice(context, context)

        handler = self._handlers_by_type[obj_type]
        with self._db_client.connect(context, table_slice) as conn:
            obj_db = handler.db_safe_transformations(context, obj, conn)
            handler.validate_obj_db(context, obj_db, conn)

            context.log.debug("all validation successful")
            super().handle_output(context, obj)
            t1 = time.perf_counter()
            context.add_output_metadata(
                {
                    **handler.metadata(context, obj, obj_db, conn),
                    "io_time": dg.FloatMetadataValue(t1 - t0),
                }
            )

    def load_input(self, context: dg.InputContext) -> object:
        t0 = time.perf_counter()

        obj_type = context.dagster_type.typing_type
        if obj_type is Any and self._default_load_type is not None:
            load_type = self._default_load_type
        else:
            load_type = obj_type

        self._check_supported_type(load_type)

        table_slice = self._get_table_slice(
            context, cast(dg.OutputContext, context.upstream_output)
        )

        with self._db_client.connect(context, table_slice) as conn:
            obj = self._handlers_by_type[load_type].load_input(
                context, table_slice, conn
            )  # type: ignore  # (pyright bug)
            t1 = time.perf_counter()

            context.add_input_metadata(
                {
                    **self._handlers_by_type[load_type].metadata(
                        cast(dg.OutputContext, context.upstream_output),
                        obj,
                        None,
                        connection=conn,
                    ),
                    "io_time": dg.FloatMetadataValue(t1 - t0),
                }
            )
        return obj


def build_custom_db_io_manager(
    io_manager_base: dg.ConfigurableIOManagerFactory,
    db_client: DbClient,
    type_handlers: Sequence[CustomDbTypeHandler],
    default_load_type: Optional[Type] = None,
    io_manager_name: str = "CustomDbIoManager",
) -> dg.IOManagerDefinition:
    @dg.io_manager(config_schema=io_manager_base.to_config_schema())
    def duckdb_io_manager(init_context):
        return CustomDbIOManager(
            type_handlers=type_handlers,
            db_client=db_client,
            io_manager_name=io_manager_name,
            database=init_context.resource_config["database"],
            schema=init_context.resource_config.get("schema"),
            default_load_type=default_load_type,
        )

    return duckdb_io_manager
