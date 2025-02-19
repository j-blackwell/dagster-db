from typing import Optional
import pandas as pd
import numpy as np
import dagster as dg


def get_sample_md(
    obj: pd.DataFrame,
    n_max=10,
    dtypes: Optional[dict[str, str]] = None,
) -> Optional[str]:
    if dtypes is None:
        dtypes = obj.dtypes.to_dict()

    cols_and_types = []
    for col in obj.columns:
        col_and_type = f"{col} <br>**_\\<{obj[col].dtype}\\>_**"
        cols_and_types.append(col_and_type)

    df = obj.copy()
    df.columns = cols_and_types
    return (
        df.sample(n=min(n_max, obj.shape[0])).astype("string").fillna("").to_markdown()
    )


def get_summary_md(obj: pd.DataFrame) -> Optional[str]:
    return obj.describe(include="all", exclude=["O", "B"]).fillna(np.inf).to_markdown()


def get_table_schema(obj: pd.DataFrame) -> dg.TableSchema:
    return dg.TableSchema(
        columns=[
            dg.TableColumn(name=name, type=str(dtype))
            for name, dtype in obj.dtypes.items()
        ]
    )


def glimpse(df: pd.DataFrame) -> str:
    string = f"""Rows: {df.shape[0]}\nColumns: {df.shape[1]}\n\n"""
    for col in df.columns:
        string += f"$ {col} <{df[col].dtype}> {df[col].head().to_numpy()}\n"

    return string
