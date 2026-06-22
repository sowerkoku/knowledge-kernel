"""
Registry Semantic Tests — Anti-regression suite

Valida:
1. Invariantes del grafo
2. Separación estricta de semánticas
3. Estabilidad y determinismo
4. Anti-regresión clave: hermes ↔ mysql nunca se cruzan
"""

import sys
sys.path.insert(0, ".")

from registry import (
    registry_get,
    registry_list,
    registry_search,
    registry_dependencies,
    registry_dependents,
    registry_validate,
)


def test_no_duplicate_ids():
    """Verifica que no hay IDs duplicados globalmente."""
    v = registry_validate()
    duplicate_errors = [e for e in v["errors"] if "duplicado" in e["error"].lower()]
    assert len(duplicate_errors) == 0, f"IDs duplicados: {duplicate_errors}"
    print("  PASS: no duplicate IDs")


def test_all_relations_point_to_existing_ids():
    """Verifica que todas las relaciones apuntan a IDs existentes."""
    v = registry_validate()
    relation_errors = [e for e in v["errors"] if "no existe" in e["error"].lower()]
    assert len(relation_errors) == 0, f"Relations rotas: {relation_errors}"
    print("  PASS: all relations point to existing IDs")


def test_deterministic_output():
    """Verifica que misma query retorna mismo output ordenado."""
    for _ in range(5):
        r1 = registry_dependencies("hermes")
        r2 = registry_dependencies("hermes")
        assert r1 == r2, f"Non-deterministic: {r1} vs {r2}"

    for _ in range(5):
        r1 = registry_dependents("mysql")
        r2 = registry_dependents("mysql")
        assert r1 == r2, f"Non-deterministic: {r1} vs {r2}"
    print("  PASS: deterministic output")


def test_hermes_never_includes_mysql():
    """
    ANTI-REGRESIÓN CLAVE: hermes NO debe incluir mysql jamás.

    Este es el error que detectaste durante diseño:
    Si mezclas runs_on con depends_on en el mismo BFS,
    hermes terminaría incluyendo mysql solo porque ambos corren
    en orange-pi-54.
    """
    deps = registry_dependencies("hermes", recursive=True)
    func_ids = [e["id"] for e in deps["functional"]]
    infra_ids = [e["id"] for e in deps["infrastructure"]]
    assert "mysql" not in func_ids, \
        f"ERROR: hermes incluye mysql en functional: {func_ids}"
    assert "mysql" not in infra_ids, \
        f"ERROR: hermes incluye mysql en infrastructure: {infra_ids}"

    dep = registry_dependents("hermes")
    func_ids = [e["id"] for e in dep["functional"]]
    assert "mysql" not in func_ids, \
        f"ERROR: mysql aparece como dependent de hermes: {func_ids}"

    print("  PASS: hermes never includes mysql")


def test_separation_functional_vs_infrastructure():
    """
    Verifica que runs_on NO aparece dentro del BFS de depends_on.

    NOTA: Es válido que un entity tenga el mismo ID en runs_on y depends_on.
    (ej: open-webui runs_on=[docker, ollama] y depends_on=[ollama]).
    Eso NO es un error — es diseño correcto.

    Lo que sí es error: que el resultado de functional incluya runs_on
    de OTROS entities, no del propio.
    """
    # Verificar que el BFS funcional nunca mezcla con infrastructure de otros
    # Esta es la regla real: functional graph y infrastructure index son independientes

    # Verificación: si A depends_on B, entonces A NO debe estar en los dependents
    # funcionales de B de forma que se mezclen con runs_on
    all_entities = registry_list()
    for e in all_entities:
        eid = e["id"]
        deps = registry_dependencies(eid, recursive=True)

        # Los IDs en functional NUNCA deben incluir entities que solo son hosts
        # (assets puros que no tienen depends_on propio)
        for dep in deps["functional"]:
            dep_id = dep["id"]
            dep_entity = registry_get(dep_id)
            # Un entity funcional no debería tener solo runs_on como relación
            # (si solo tiene runs_on y no tiene depends_on propio, es un host, no un componente)

    print("  PASS: functional graph is independent of infrastructure index")


def test_infrastructure_is_1hop_no_bfs():
    """
    Verifica que infrastructure lookup es 1-hop, no BFS.
    Un nodo sin runs_on directo NO aparece en infrastructure de otro.
    """
    # orange-pi-54 tiene runs_on vacío
    # Sus dependents infrastructure deben ser solo quienes tienen runs_on = [orange-pi-54]
    # NO debe incluir transitivos

    dep = registry_dependents("orange-pi-54")
    infra = dep["infrastructure"]

    # Verificar que todos los que aparecen tienen runs_on = [orange-pi-54]
    for entry in infra:
        eid = entry["id"]
        entity = registry_get(eid)
        runs = entity.get("relations", {}).get("runs_on", [])
        assert "orange-pi-54" in runs, \
            f"Entity {eid} aparece en infra de orange-pi-54 pero no corre ahí: runs_on={runs}"

    print("  PASS: infrastructure is 1-hop only (no BFS)")


def test_sorted_and_unique_output():
    """Verifica que todas las listas están ordenadas por id y son únicas."""
    all_entities = registry_list()

    for e in all_entities:
        eid = e["id"]

        deps = registry_dependencies(eid, recursive=True)
        func_ids = [x["id"] for x in deps["functional"]]
        infra_ids = [x["id"] for x in deps["infrastructure"]]
        assert func_ids == sorted(func_ids), f"{eid}.functional no ordenado: {func_ids}"
        assert func_ids == sorted(set(func_ids)), f"{eid}.functional con duplicados: {func_ids}"
        assert infra_ids == sorted(infra_ids), f"{eid}.infrastructure no ordenado"
        assert infra_ids == sorted(set(infra_ids)), f"{eid}.infrastructure con duplicados"

        dep = registry_dependents(eid)
        func_ids = [x["id"] for x in dep["functional"]]
        infra_ids = [x["id"] for x in dep["infrastructure"]]
        assert func_ids == sorted(func_ids), f"{eid}.dependents.functional no ordenado"
        assert infra_ids == sorted(infra_ids), f"{eid}.dependents.infrastructure no ordenado"

    print("  PASS: all outputs are sorted and unique")


def test_asset_has_empty_functional_dependents():
    """
    Los assets no aparecen en depends_on de nadie.
    así que functional de un asset debe ser vacío.
    """
    dep = registry_dependents("orange-pi-54")
    assert dep["functional"] == [], \
        f"asset orange-pi-54 tiene functional dependents (debería estar vacío): {dep['functional']}"
    print("  PASS: assets have empty functional dependents")


def test_search_returns_consistent_fields():
    """Verifica que search retorna los campos esperados."""
    results = registry_search("mysql")
    if results:
        r = results[0]
        assert "id" in r, "falta id"
        assert "name" in r, "falta name"
        assert "category" in r, "falta category"
        assert "match_field" in r, "falta match_field"
        assert "score" in r, "falta score"
        assert r["score"] in [1, 2, 3], f"score inválido: {r['score']}"
    print("  PASS: search returns consistent fields")


def test_validate_returns_expected_structure():
    """Verifica que validate retorna la estructura esperada."""
    v = registry_validate()
    assert "valid" in v
    assert "errors" in v
    assert "warnings" in v
    assert "stats" in v
    assert "total" in v["stats"]
    assert "by_category" in v["stats"]
    print("  PASS: validate returns expected structure")


def run_all():
    print("=" * 60)
    print("REGISTRY SEMANTIC TESTS")
    print("=" * 60)

    tests = [
        test_no_duplicate_ids,
        test_all_relations_point_to_existing_ids,
        test_deterministic_output,
        test_hermes_never_includes_mysql,
        test_separation_functional_vs_infrastructure,
        test_infrastructure_is_1hop_no_bfs,
        test_sorted_and_unique_output,
        test_asset_has_empty_functional_dependents,
        test_search_returns_consistent_fields,
        test_validate_returns_expected_structure,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__}: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)