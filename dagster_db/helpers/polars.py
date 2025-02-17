from typing import Optional
import polars as pl
import numpy as np
import dagster as dg

from dagster_db.helpers.pandas import get_sample_md as get_sample_md_pd


def get_sample_md(obj: pl.DataFrame, n_max=10) -> Optional[str]:
    obj_pd = obj.sample(min(n_max, obj.height)).to_pandas()
    return get_sample_md_pd(obj_pd, n_max=n_max)


def get_summary_md(obj: pl.DataFrame) -> Optional[str]:
    try:
        return (
            obj.select(
                [
                    key
                    for key, value in obj.schema.items()
                    if value not in [pl.Utf8, pl.Boolean]
                ]
            )
            .describe()
            .to_pandas()
            .set_index("statistic")
            .fillna(np.inf)
            .to_markdown()
        )
    except TypeError:
        # No numeric columns
        return "No numeric columns to summarise"


def get_table_schema(obj: pl.DataFrame) -> dg.TableSchema:
    return dg.TableSchema(
        columns=[
            dg.TableColumn(name=name, type=str(dtype))
            for name, dtype in zip(obj.columns, obj.dtypes)
        ]
    )
