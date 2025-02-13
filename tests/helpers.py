import dagster as dg


def result_metadata(result: dg.ExecuteInProcessResult, node: str):
    materialisation = result.asset_materializations_for_node(node)
    metadata = materialisation[0].metadata
    return metadata
