"""Small declared catalogs for unit-level MinDiff projection contracts."""

from collections.abc import Mapping, Sequence

from src.counterexample.mindiff import PredicateProjectionContract


def projection_contract(
    projections: Mapping[str, str],
    witness_variables: Sequence[str] | Mapping[str, object],
) -> PredicateProjectionContract:
    """Bind synthetic unit predicates through a declared action catalog."""

    actions = []
    bindings = {}
    for index, (variable, predicate) in enumerate(projections.items(), start=1):
        action_id = f"unit-projection-action-{index}"
        bindings[variable] = action_id
        actions.append(
            {
                "action_id": action_id,
                "observation_model": {"world_dependencies": [predicate]},
            }
        )
    catalog = {
        "schema_version": "0.8.0",
        "catalog_id": "unit-projection-catalog",
        "catalog_version": "0.8.0",
        "actions": actions,
    }
    document = {
        "schema_version": "0.8.0",
        "contract_id": "unit-projection-contract",
        "catalog_id": catalog["catalog_id"],
        "catalog_version": catalog["catalog_version"],
        "bindings": bindings,
    }
    return PredicateProjectionContract.from_action_catalog(
        document, catalog, witness_variables=witness_variables
    )
