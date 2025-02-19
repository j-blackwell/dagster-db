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
    """
    Not always supposed to be valid SQL, but to test common uses.
    """
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

    query_expr = SqlQuery("SELECT {{ my_expr }}", my_expr=SqlExpr("RANDOM()"))
    assert query_expr.render() == "SELECT RANDOM()"

    query_col = SqlQuery("SELECT {{ my_col }}", my_col=SqlColumn("my_col"))
    assert query_col.render() == "SELECT `my_col`"

    query_nested = SqlQuery("SELECT {{ query_int }}", query_int=query_int)
    assert query_nested.render() == "SELECT (SELECT 1)"

    query_list_int = SqlQuery("SELECT {{ my_list }}", my_list=[1, 2])
    assert query_list_int.render() == "SELECT (1, 2)"

    query_list_str = SqlQuery("SELECT {{ my_list }}", my_list=["1", "2"])
    assert query_list_str.render() == "SELECT ('1', '2')"

    query_list_expr = SqlQuery(
        "SELECT {{ my_list }}",
        my_list=[
            SqlExpr("RANDOM()"),
            SqlExpr("CASE WHEN RANDOM() > 0.5 THEN 1 ELSE 0 END"),
        ],
    )
    assert (
        query_list_expr.render()
        == "SELECT RANDOM(),\nCASE WHEN RANDOM() > 0.5 THEN 1 ELSE 0 END"
    )

    query_list_col = SqlQuery(
        "SELECT {{ my_list }}",
        my_list=[SqlColumn("my_col"), SqlColumn("my_col1")],
    )
    assert query_list_col.render() == "SELECT `my_col`,\n`my_col1`"

    query_list_mix = SqlQuery(
        "SELECT {{ my_list }}",
        my_list=[SqlColumn("my_col"), SqlExpr("RANDOM()")],
    )
    assert query_list_mix.render() == "SELECT `my_col`,\nRANDOM()"

    query_list_mix_bad = SqlQuery(
        "SELECT {{ my_list }}",
        my_list=[SqlColumn("my_col"), "test"],
    )
    with pytest.raises(ValueError):
        query_list_mix_bad.render()


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


def test_sql_query_complex_jinja():
    query = SqlQuery(
        """{% set columns = [ 'last_name', 'username', 'email' ] %}
{%- for value in columns %}
	{{ value }}
	{%- if not loop.last -%},{% endif -%}
{% endfor %}"""
    )

    query_rendered_expected = "\n\tlast_name," "\n\tusername," "\n\temail"
    assert query.render() == query_rendered_expected

    query = SqlQuery(
        """{% for payment_method in ["bank_transfer", "credit_card", "gift_card"] %}
sum(case when payment_method = '{{payment_method}}' then amount end) as {{payment_method}}_amount,
{% endfor %}"""
    )

    query_rendered_expected = (
        "\nsum(case when payment_method = 'bank_transfer' then amount end) as bank_transfer_amount,\n"
        "\nsum(case when payment_method = 'credit_card' then amount end) as credit_card_amount,\n"
        "\nsum(case when payment_method = 'gift_card' then amount end) as gift_card_amount,\n"
    )
    assert query.render() == query_rendered_expected
