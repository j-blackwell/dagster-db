import dagster as dg
from abc import abstractmethod
from typing import Any, Generic, Sequence, Type, TypeVar

from dagster._core.storage.db_io_manager import DbTypeHandler
from dagster._core.storage.db_io_manager import TableSlice

Obj = TypeVar("Obj")
Conn = TypeVar("Conn")


class CustomDbTypeHandler(DbTypeHandler, Generic[Obj, Conn]):
    """
    Base-class to be used when creating type handlers that follow the
    logic of the `custom_db_io_manager`.
    """

    @abstractmethod
    def validate_obj_db(self, context, obj_db: Obj, connection: Conn):
        pass

    @abstractmethod
    def db_safe_transformations(self, context, obj: Obj, connection: Conn) -> Obj:
        pass

    @abstractmethod
    def output_metadata(
        self,
        context: dg.OutputContext,
        obj: Obj,
        obj_db: Obj,
        connection: Conn,
    ) -> dict[str, dg.MetadataValue]:
        pass

    @abstractmethod
    def handle_output(
        self,
        context: dg.OutputContext,
        table_slice: TableSlice,
        obj: Obj,
        connection: Conn,
    ):
        pass

    @abstractmethod
    def load_input(
        self,
        context: dg.InputContext,
        table_slice: TableSlice,
        connection: Conn,
    ) -> Obj:
        pass

    @property
    @abstractmethod
    def supported_types(self) -> Sequence[Type[object]]:
        pass
