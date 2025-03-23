import dagster as dg
from typing import Sequence, Type
from dagster._core.storage.db_io_manager import TableSlice
import pandas as pd
from dagster_db.exceptions.failures import DbTablesIncompatibleFailure
from duckdb import BinderException, DuckDBPyConnection, IOException
from dagster_duckdb.io_manager import DuckDbClient
from dagster._utils.backoff import backoff

from dagster_db.helpers.duckdb import execute_duckdb
from dagster_db.helpers.generic_db import table_slice_to_schema_table
from dagster_db.helpers.pandas import get_sample_md, get_table_schema, glimpse
from dagster_db.query.sql_query import SqlExpr, SqlQuery
from dagster_db.type_handlers.custom_type_handler import CustomDbTypeHandler


class DuckDbPandasTypeHandler(CustomDbTypeHandler[pd.DataFrame, DuckDBPyConnection]):
    """
    Base-class for duckdb-pandas type handler that handles read/write, and adds
    metadata, but doesn't include object validation or db_safe_transformations.
    """

    @property
    def supported_types(self) -> Sequence[Type[object]]:
        return [pd.DataFrame]

    def validate_obj_db(
        self, context, obj_db: pd.DataFrame, connection: DuckDBPyConnection
    ):
        return

    def db_safe_transformations(
        self, context, obj: pd.DataFrame, connection: DuckDBPyConnection
    ) -> pd.DataFrame:
        return obj

    def metadata(
        self,
        context: dg.OutputContext,
        obj: pd.DataFrame,
        obj_db: pd.DataFrame,
        connection: DuckDBPyConnection,
    ):
        return {
            "sample_obj": dg.MarkdownMetadataValue(get_sample_md(obj)),
            **(
                {"sample_obj_db": dg.MarkdownMetadataValue(get_sample_md(obj_db))}
                if obj_db is not None
                else {}
            ),
            **(
                {"table_schema": dg.TableSchemaMetadataValue(get_table_schema(obj_db))}
                if obj_db is not None
                else {}
            ),
            "rows": dg.IntMetadataValue(obj.shape[0]),
        }

    def _load_into_db(
        self,
        table_schema,
        obj: pd.DataFrame,
        connection: DuckDBPyConnection,
    ):
        ctas_query = SqlQuery(
            "CREATE TABLE IF NOT EXISTS {{ table_schema }} AS SELECT * FROM obj;",
            table_schema=SqlExpr(table_schema),
        )
        execute_duckdb(ctas_query, connection, obj=obj)
        if not connection.fetchall():
            insert_query = SqlQuery(
                "INSERT INTO {{ table_schema }} SELECT * FROM obj",
                table_schema=SqlExpr(table_schema),
            )
            execute_duckdb(insert_query, connection, obj=obj)

    def handle_output(
        self,
        context: dg.OutputContext,
        table_slice: TableSlice,
        obj: pd.DataFrame,
        connection: DuckDBPyConnection,
    ):
        table_schema = table_slice_to_schema_table(table_slice)
        create_schema_query = SqlQuery(
            "CREATE SCHEMA IF NOT EXISTS {{ schema }}",
            schema=SqlExpr(table_slice.schema),
        )
        execute_duckdb(create_schema_query, connection)
        execute_duckdb(SqlQuery("SET GLOBAL pandas_analyze_sample=10000"), connection)
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
        except BinderException as e:
            obj_existing = self.load_input(context, table_slice, connection)
            raise DbTablesIncompatibleFailure(
                {"obj": obj, "obj_existing": obj_existing},
                connection,
            )
        return

    def load_input(
        self,
        context: dg.InputContext | dg.OutputContext,
        table_slice: TableSlice,
        connection: DuckDBPyConnection,
    ) -> pd.DataFrame:
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            raise ValueError(
                f"{table_slice.partition_dimensions=} incompatible with {context.asset_partition_keys=}"
            )

        query = DuckDbClient.get_select_statement(table_slice)
        obj = execute_duckdb(SqlQuery(query), connection, return_type=pd.DataFrame)
        return obj
