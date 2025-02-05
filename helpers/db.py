def table_slice_to_schema_table(table_slice, sep="."):
    return table_slice.schema + sep + table_slice.table
