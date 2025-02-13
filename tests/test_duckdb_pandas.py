from typing import Any
import dagster as dg
import pandas as pd

from tests.helpers import result_metadata


def test_duckdb_pandas_simple(resources: dict[str, Any]):
    @dg.asset
    def test_duckdb_pandas_asset(context: dg.AssetExecutionContext) -> pd.DataFrame:
        df = pd.DataFrame({"a": [1, 2, 3], "b": [2, 3, 4]})
        return df

    result = dg.materialize([test_duckdb_pandas_asset], resources=resources)
    assert result.success

    metadata = result_metadata(result, "test_duckdb_pandas_asset")
    assert "sample_obj" in metadata.keys()
    assert "sample_obj_db" in metadata.keys()
    assert "rows" in metadata.keys()


def test_duckdb_pandas_downstream(resources: dict[str, Any]):
    @dg.asset
    def test_duckdb_pandas_asset(context: dg.AssetExecutionContext) -> pd.DataFrame:
        df = pd.DataFrame({"a": [1, 2, 3], "b": [2, 3, 4]})
        return df

    @dg.asset
    def test_duckdb_pandas_asset_downstream(
        context: dg.AssetExecutionContext,
        test_duckdb_pandas_asset: pd.DataFrame,
    ) -> pd.DataFrame:
        test_duckdb_pandas_asset_downstream = test_duckdb_pandas_asset.assign(
            c=["a", "b", "c"]
        )
        return test_duckdb_pandas_asset_downstream

    result = dg.materialize(
        [test_duckdb_pandas_asset, test_duckdb_pandas_asset_downstream],
        resources=resources,
    )
    assert result.success
