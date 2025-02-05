from typing import (
    Optional,
    Sequence,
    Type,
    Any,
)

from dagster._core.storage.db_io_manager import DbIOManager, DbClient
import dagster as dg

from type_handlers.custom_type_handler import CustomDbTypeHandler


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
        # TODO: validate type_handlers
        # TODO: don't inherit init?

        super().__init__(
            type_handlers=type_handlers,
            db_client=db_client,
            database=database,
            schema=schema,
            io_manager_name=io_manager_name,
            default_load_type=default_load_type,
        )

        self._handlers_by_type: dict[type[Any], CustomDbTypeHandler] # type: ignore

    def handle_output(self, context: dg.OutputContext, obj: object) -> None:
        obj_type = type(obj)
        self._check_supported_type(obj_type)
        table_slice = self._get_table_slice(context, context)

        handler = self._handlers_by_type[obj_type]
        with self._db_client.connect(context, table_slice) as conn:
            obj_db = handler.db_safe_transformations(context, obj, conn)
            handler.validate_obj_db(context, obj_db, conn)

        context.log.debug("all validation successful")
        super().handle_output(context, obj)
        context.add_output_metadata(handler.output_metadata(context, obj, obj_db))

    def load_input(self, context: dg.InputContext) -> object:
        return super().load_input(context)
