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

    Args:
        template_string: Jinja2-template string to be rendered.
        sql_dialect: The SQL dialect that the query is written in so it can be translated to the
            database-specific dialect.
        **kwargs: bindings for the template.
    """

    def __init__(self, template_string: str, sql_dialect: str = "duckdb", **kwargs):
        env = Environment(undefined=StrictUndefined)
        self.template: Template = env.from_string(template_string)
        self.sql_dialect = sql_dialect
        self.bindings = kwargs

    def add_bindings(self, *args: t.Any, **kwargs: t.Any):
        self.bindings = self.bindings | dict(*args, **kwargs)

    def _is_sql(self, value: t.Any) -> bool:
        if isinstance(value, (SqlQuery, SqlColumn, SqlExpr)):
            return True
        elif isinstance(value, (list, set)):
            values_is_sql = [self._is_sql(x) for x in value]
            if all(values_is_sql) != any(values_is_sql):
                raise ValueError(
                    f"{value=} is a list that contains a mixture of 'value' and 'sql' types."
                )
            return any(values_is_sql)
        else:
            return False

    def _render_value(self, value: t.Any) -> str:
        if isinstance(value, SqlQuery):
            return f"({value.render()})"
        elif isinstance(value, list):
            if self._is_sql(value):
                sep = ",\n"
                format_str = "{}"
            else:
                sep = ", "
                format_str = "({})"

            values_list = [self._render_value(v) for v in value]
            values_rendered = sep.join(values_list)
            return format_str.format(values_rendered)
        elif isinstance(value, (dt.datetime, dt.date, Timestamp)):
            return f"'{str(value)}'"
        elif isinstance(value, str):
            try:
                return self._render_value(Timestamp(value))
            except ValueError:
                return f"'{value}'"
        elif isinstance(value, (SqlExpr, SqlColumn)):
            return value.value
        else:
            return str(value)

    def render(self, *args: t.Any, **kwargs: t.Any) -> str:
        """Render all bindings in the query string."""
        bindings_original = self.bindings | dict(*args, **kwargs)

        bindings_curated = {}
        for key, value in bindings_original.items():
            bindings_curated[key] = self._render_value(value)

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
