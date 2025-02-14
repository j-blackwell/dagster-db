import datetime as dt
from jinja2 import Template, StrictUndefined, Environment
from pandas import Timestamp
import typing as t


class SqlQuery:
    """
    Stores bindings for, and renders Jinja2-templated queries for use with SQL
    databases.
    Has type-specific rules for rendering bindings of different types.

    e.g. lists are converted into SQL syntax, SQL queries can be rendered
    inside other queries,
    and string values are wrapped in quotes so that they are not forgotten
    every time when working with strings.
    As a result, SqlExpr and SqlColumn have been created to allow no qoutes,
    or back-ticks (or another column name identifier) to be added when rendered.

    :param template_string: Jinja2-template string to be rendered.
    :**kwargs: bindings for the template.
    """

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
    """
    Create a SQL expression that will be rendered as-is.
    """

    def __init__(self, value: str):
        self.value = value


class SqlColumn:
    """
    Refer to a column within SQL by using the databases column identifier
    (usually a back-tick).
    This will mean that quotes are not added when rendered.
    """

    def __init__(self, value: str, identifier: str = "`"):
        self.value = f"{identifier}{value}{identifier}"
