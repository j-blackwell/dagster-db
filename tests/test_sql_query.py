import datetime as dt

from jinja2.exceptions import UndefinedError
import pytest
from pandas import Timestamp
from dagster_db import SqlQuery, SqlExpr, SqlColumn


def test_sql_query_noop():
    base_query = "SELECT * FROM my_table"
    query = SqlQuery(base_query)
    assert query.render() == base_query


def test_sql_query_unbound():
    query = SqlQuery("SELECT {{ my_int }}")
    with pytest.raises(UndefinedError):
        query.render()


def test_sql_query_simple():
    query_int = SqlQuery("SELECT {{ my_int }}", my_int=1)
    assert query_int.render() == "SELECT 1"

    query_str = SqlQuery("SELECT {{ my_str }}", my_str="1")
    assert query_str.render() == "SELECT '1'"

    query_dt = SqlQuery("SELECT {{ my_dt }}", my_dt="2023-01-01")
    assert query_dt.render() == "SELECT '2023-01-01 00:00:00'"

    query_dt1 = SqlQuery("SELECT {{ my_dt }}", my_dt=dt.datetime(2023, 1, 1))
    assert query_dt1.render() == "SELECT '2023-01-01 00:00:00'"

    query_dt2 = SqlQuery("SELECT {{ my_dt }}", my_dt=dt.date(2023, 1, 1))
    assert query_dt2.render() == "SELECT '2023-01-01'"

    query_dt3 = SqlQuery("SELECT {{ my_dt }}", my_dt=Timestamp("2023-01-01"))
    assert query_dt3.render() == "SELECT '2023-01-01 00:00:00'"

    query_list = SqlQuery("SELECT {{ my_list }}", my_list=[1, 2])
    assert query_list.render() == "SELECT (1,2)"

    query_expr = SqlQuery("SELECT {{ my_expr }}", my_expr=SqlExpr("RANDOM()"))
    assert query_expr.render() == "SELECT RANDOM()"

    query_col = SqlQuery("SELECT {{ my_col }}", my_col=SqlColumn("my_col"))
    assert query_col.render() == "SELECT `my_col`"

    query_nested = SqlQuery("SELECT {{ query_int }}", query_int=query_int)
    assert query_nested.render() == "SELECT (SELECT 1)"


def test_sql_query_methods():
    query = SqlQuery("SELECT {{ my_int }}", my_int=1)
    assert query.bindings == {"my_int": 1}

    query = SqlQuery("SELECT {{ my_int }}")
    query.add_bindings({"my_int": 1})
    assert query.bindings == {"my_int": 1}

    query = SqlQuery("SELECT {{ my_int }}")
    query.add_bindings(my_int=1)
    assert query.bindings == {"my_int": 1}

    # no error
    query = SqlQuery("SELECT {{ my_int }}")
    query.render(my_int=1)
