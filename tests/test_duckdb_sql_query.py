from typing import Any
import dagster as dg

from dagster_db import SqlQuery
from tests.helpers import result_metadata


def test_duckdb_sql_query_simple(resources: dict[str, Any]):
    @dg.asset
    def test_duckdb_sql_query_asset(context: dg.AssetExecutionContext) -> SqlQuery:
        query = SqlQuery("SELECT 1 AS a, 2 AS b")
        context.log.info(query.render())
        return query

    result = dg.materialize([test_duckdb_sql_query_asset], resources=resources)
    assert result.success

    metadata = result_metadata(result, "test_duckdb_sql_query_asset")
    assert "sample_obj" in metadata.keys()
    assert "sample_obj_db" in metadata.keys()
    assert "rows" in metadata.keys()
    assert "query_rendered" in metadata.keys()


def test_duckdb_sql_query_downstream(resources: dict[str, Any]):
    @dg.asset
    def test_duckdb_sql_query_asset(context: dg.AssetExecutionContext) -> SqlQuery:
        query = SqlQuery("SELECT 1 AS a, 2 AS b")
        return query

    @dg.asset
    def test_duckdb_sql_query_asset_downstream(
        context: dg.AssetExecutionContext,
        test_duckdb_sql_query_asset: SqlQuery,
    ) -> SqlQuery:
        query = SqlQuery(
            "SELECT *, 3 AS c FROM {{ test_duckdb_sql_query_asset }}",
            test_duckdb_sql_query_asset=test_duckdb_sql_query_asset,
        )
        return query

    result = dg.materialize(
        [test_duckdb_sql_query_asset, test_duckdb_sql_query_asset_downstream],
        resources=resources,
    )
    assert result.success
