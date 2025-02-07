import dagster as dg
from typing import Sequence, Type
from dagster._core.storage.db_io_manager import TableSlice
import pandas as pd
from duckdb import BinderException, DuckDBPyConnection, IOException
from dagster_duckdb.io_manager import DuckDbClient
from dagster._utils.backoff import backoff

from dagster_db.helpers.db import table_slice_to_schema_table
from dagster_db.helpers.pandas import get_sample_md, get_table_schema, glimpse
from dagster_db.type_handlers.custom_type_handler import CustomDbTypeHandler

class DuckDbPandasTypeHandler(CustomDbTypeHandler[pd.DataFrame, DuckDBPyConnection]):

    @property
    def supported_types(self) -> Sequence[Type[object]]:
        return [pd.DataFrame]

    def validate_obj_db(self, context, obj_db: pd.DataFrame, connection: DuckDBPyConnection):
        return

    def db_safe_transformations(self, context, obj: pd.DataFrame, connection: DuckDBPyConnection) -> pd.DataFrame:
        return obj

    def output_metadata(self, context: dg.OutputContext, obj: pd.DataFrame, obj_db: pd.DataFrame):
        return {
            "sample_obj": dg.MarkdownMetadataValue(get_sample_md(obj)),
            "sample_obj_db": dg.MarkdownMetadataValue(get_sample_md(obj_db)),
            "rows": dg.IntMetadataValue(obj.shape[0]),
            "table_schema": dg.TableSchemaMetadataValue(get_table_schema(obj_db)),
            }

    @classmethod
    def _load_into_db(table_schema, obj: pd.DataFrame, connection: DuckDBPyConnection):
        connection.execute(f"CREATE TABLE IF NOT EXISTS {table_schema} as SELECT * FROM obj;")
        if not connection.fetchall():
            connection.execute(f"INSERT INTO {table_schema} SELECT * FROM obj;")


    def handle_output(self, context: dg.OutputContext, table_slice: TableSlice, obj: pd.DataFrame, connection: DuckDBPyConnection):
        table_schema = table_slice_to_schema_table(table_slice)
        connection.execute(f"CREATE SCHEMA IF NOT EXISTS {table_slice.schema};")
        connection.execute("SET GLOBAL pandas_analyze_sample=10000")
        try:
            backoff(
                self._load_into_db,
                retry_on=(IOException,),
                kwargs={
                    "table_schema": table_schema,
                    "obj": obj,
                    "connection": connection,
                },
                max_retries=1,
            )
        except BinderException:
            obj_existing = self.load_input(context, table_slice, connection)
            msg = f"""`obj` incompatible with existing table

            `obj`
            {glimpse(obj)}

            `obj_existing`
            {glimpse(obj_existing)}
            """
            context.log.error(msg)
        return

    def load_input(self, context: dg.InputContext | dg.OutputContext, table_slice: TableSlice, connection: DuckDBPyConnection) -> pd.DataFrame:
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            raise ValueError(f"{table_slice.partition_dimensions=} incompatible with {context.asset_partition_keys=}")

        query = DuckDbClient.get_select_statement(table_slice)
        result = connection.execute(query=query)
        obj = result.df()
        glimpse(obj)
        return obj
