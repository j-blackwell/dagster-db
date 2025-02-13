import datetime as dt
from jinja2 import Template, StrictUndefined, Environment
from pandas import Timestamp
import typing as t


class SqlQuery:
    def __init__(self, template_string: str, **kwargs):
        env = Environment(undefined=StrictUndefined)
        self.template: Template = env.from_string(template_string)
        self.bindings = kwargs

    def add_bindings(self, *args: t.Any, **kwargs: t.Any):
        self.bindings = self.bindings | dict(*args, **kwargs)

    def render(self, *args: t.Any, **kwargs: t.Any) -> str:
        bindings_original = self.bindings | dict(*args, **kwargs)

        bindings_curated = {}
        for key, value in bindings_original.items():
            if isinstance(value, SqlQuery):
                bindings_curated[key] = f"({value.render()})"
            elif isinstance(value, list):
                values_list = [
                    f"'{x}'" if isinstance(x, str) else str(x) for x in value
                ]
                bindings_curated[key] = f"({','.join(values_list)})"
            elif isinstance(value, (dt.datetime, dt.date, Timestamp)):
                bindings_curated[key] = f"'{str(value)}'"
            elif isinstance(value, str):
                try:
                    value_dt = Timestamp(value)
                    bindings_curated[key] = f"'{str(value_dt)}'"
                except ValueError:
                    bindings_curated[key] = f"'{value}'"
            elif isinstance(value, (SqlExpr, SqlColumn)):
                bindings_curated[key] = value.value
            else:
                bindings_curated[key] = value

        return self.template.render(**bindings_curated)

    @property
    def markdown(self) -> str:
        return f"```sql\n{self.render()}\n```"


class SqlExpr:
    def __init__(self, value: str):
        self.value = value


class SqlColumn:
    def __init__(self, value: str, identifier: str = "`"):
        self.value = f"{identifier}{value}{identifier}"
