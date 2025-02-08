from jinja2 import Template, StrictUndefined, Environment
from pandas import Timestamp
import typing as t


class SqlQuery(Template):
    def __init__(self, template_string: str):
        env = Environment(undefined=StrictUndefined)
        self.template = env.from_string(template_string)

    def add_bindings(self, *args: t.Any, **kwargs: t.Any):
        if len(args) == 1:
            self.bindings = kwargs | args[0]
        else:
            self.bindings = kwargs

    def render(self, *args: t.Any, **kwargs: t.Any) -> str:
        try:
            bindings_original = self.bindings | kwargs
        except AttributeError:
            bindings_original = kwargs

        if len(args) == 1:
            bindings_original = bindings_original | args[0]

        bindings = {}
        for key, value in bindings_original.items():
            if isinstance(value, SqlQuery):
                bindings[key] = f"({value.render()})"
            elif isinstance(value, list):
                values_list = [
                    f"'{x}'" if isinstance(x, str) else str(x) for x in value
                ]
                bindings[key] = f"({','.join(values_list)})"
            elif isinstance(value, str):
                try:
                    value_dt = Timestamp(value)
                    bindings[key] = f"'{str(value_dt)}'"
                except ValueError:
                    bindings[key] = f"'{value}'"
            else:
                bindings[key] = value

        return self.template.render(**bindings)
