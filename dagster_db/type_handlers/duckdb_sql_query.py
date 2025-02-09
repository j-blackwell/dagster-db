import dagster as dg
from typing import Sequence, Type
from dagster._core.storage.db_io_manager import TableSlice
from duckdb import BinderException, DuckDBPyConnection, IOException
from dagster_duckdb.io_manager import DuckDbClient
from dagster._utils.backoff import backoff

from dagster_db.helpers.generic_db import table_slice_to_schema_table
from dagster_db.helpers.duckdb import execute_duckdb
from dagster_db.helpers.sql_query import get_sample_md, get_table_schema, get_rows, glimpse
from dagster_db.type_handlers.custom_type_handler import CustomDbTypeHandler
from dagster_db.query.sql_query import SqlQuery


class DuckDbQueryTypeHandler(CustomDbTypeHandler[SqlQuery, DuckDBPyConnection]):
    @property
    def supported_types(self) -> Sequence[Type[object]]:
        return [SqlQuery]

    def validate_obj_db(
        self,
        context,
        obj_db: SqlQuery,
        connection: DuckDBPyConnection,
    ):
        return

    def db_safe_transformations(
        self,
        context,
        obj: SqlQuery,
        connection: DuckDBPyConnection,
    ) -> SqlQuery:
        return obj

    def output_metadata(
        self,
        context: dg.OutputContext,
        obj: SqlQuery,
        obj_db: SqlQuery,
        connection: DuckDBPyConnection,
    ):
        return {
            "sample_obj": dg.MarkdownMetadataValue(get_sample_md(obj, connection)),
            "sample_obj_db": dg.MarkdownMetadataValue(get_sample_md(obj_db, connection)),
            "rows": dg.IntMetadataValue(get_rows(obj, connection)),
            "table_schema": dg.TableSchemaMetadataValue(get_table_schema(obj, connection)),
        }

    def _load_into_db(
        self,
        table_schema,
        obj: SqlQuery,
        connection: DuckDBPyConnection,
    ):
        ctas_query = SqlQuery("CREATE TABLE IF NOT EXISTS {{ table_schema }} AS SELECT * FROM {{ obj }}", table_schema=table_schema, obj=obj)
        execute_duckdb(ctas_query, connection)
        if not connection.fetchall():
            insert_query = SqlQuery("INSERT INTO {{ table_schema }} SELECT * FROM {{ obj }}", table_schema=table_schema, obj=obj)
            execute_duckdb(insert_query, connection)

    def handle_output(
        self,
        context: dg.OutputContext,
        table_slice: TableSlice,
        obj: SqlQuery,
        connection: DuckDBPyConnection,
    ):
        table_schema = table_slice_to_schema_table(table_slice)
        create_schema_query = SqlQuery("CREATE SCHEMA IF NOT EXISTS {{ schema }}", schema=table_slice.schema)
        execute_duckdb(create_schema_query, connection)

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
            {glimpse(obj, connection)}

            `obj_existing`
            {glimpse(obj_existing, connection)}
            """
            context.log.error(msg)

        return

    def load_input(
        self,
        context: dg.InputContext | dg.OutputContext,
        table_slice: TableSlice,
        connection: DuckDBPyConnection,
    ) -> SqlQuery:
        if table_slice.partition_dimensions and len(context.asset_partition_keys) == 0:
            raise ValueError(
                f"{table_slice.partition_dimensions=} incompatible with {context.asset_partition_keys=}"
            )

        query = DuckDbClient.get_select_statement(table_slice)
        return SqlQuery(query)
