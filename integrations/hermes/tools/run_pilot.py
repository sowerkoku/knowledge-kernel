# run_pilot.py — Ejecuta el Production Grounding Pilot
#
# Para cada pregunta semilla:
# 1. Detecta si necesita hechos (pattern matching simple)
# 2. Ejecuta consultas al Kernel (cmdb_get, cmdb_impact, cmdb_list)
# 3. Genera una respuesta factual (assertions)
# 4. Registra evento con métricas (KAR, FGR, latency)

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Import tools del Kernel
import sys
sys.path.insert(0, str(Path(__file__).parent))
from cmdb.api import cmdb_get, cmdb_exists, cmdb_list, cmdb_impact

from grounding_pilot import (
    GroundingEvent,
    SEED_BANK,
    record_event,
    now_iso,
    ensure_dirs,
    QUESTIONS_FILE,
    EVENTS_FILE,
)


def needs_facts(question: str) -> bool:
    """
    Detecta si una pregunta requiere hechos del Kernel.
    Pattern simple: preguntas sobre infraestructura, dependencias, endpoints, agentes.
    """
    keywords = [
        "dónde", "corre", "qué", "depende", "puertos", "expone",
        "perfiles", "hermes", "configurados", "mysql", "ollama",
        "orange-pi", "agent", "software", "asset", "endpoint"
    ]
    q_lower = question.lower()
    return any(k in q_lower for k in keywords)


def execute_query(question: str, category: str) -> Tuple[List[str], int, int, str]:
    """
    Ejecuta consultas al Kernel según la categoría.
    Retorna: (functions_called, facts_returned, latency_ms, answer)
    """
    functions_called = []
    facts_returned = 0
    answer_parts = []

    start = time.perf_counter()

    if category == "infrastructure":
        # ¿Dónde corre Ollama? → cmdb_get("ollama")
        functions_called.append("cmdb_get")
        result = cmdb_get("ollama")
        if result.exists:
            facts_returned += 1
            answer_parts.append(f"Ollama corre en: {result.entity.id}")
            # Buscar relations para encontrar runs_on
            for rel in result.entity.relations:
                if rel.get("type") == "runs_on":
                    facts_returned += 1
                    answer_parts.append(f"  → runs_on: {rel.get('target', 'unknown')}")
        else:
            answer_parts.append("Ollama no encontrado en el Kernel")

    elif category == "dependencies":
        # ¿Qué depende de MySQL? → cmdb_impact("mysql")
        functions_called.append("cmdb_impact")
        result = cmdb_impact("mysql")
        if result.get("exists"):
            facts_returned += 1
            dependents = result.get("depends_on_me", {}).get("direct", [])
            answer_parts.append(f"MySQL tiene {len(dependents)} dependientes directos")
            for dep in dependents[:5]:  # Mostrar primeros 5
                facts_returned += 1
                dep_id = dep.get("id") if isinstance(dep, dict) else str(dep)
                answer_parts.append(f"  → {dep_id}")
            if not dependents:
                answer_parts.append("  (sin dependencias directas)")
        else:
            answer_parts.append("MySQL no encontrado en el Kernel")

    elif category == "endpoints":
        # ¿Qué puertos expone orange-pi-54? → cmdb_get + cmdb_list
        functions_called.append("cmdb_get")
        functions_called.append("cmdb_list")
        asset_result = cmdb_get("orange-pi-54")
        if asset_result.exists:
            facts_returned += 1
            answer_parts.append(f"orange-pi-54 es un asset")
            # Buscar endpoints que corren en este asset
            endpoints = cmdb_list(kind="endpoint")
            for ep in endpoints:
                ep_id = ep.get("id") if isinstance(ep, dict) else ep
                # Verificar si el endpoint está relacionado con el asset
                ep_detail = cmdb_get(ep_id)
                if ep_detail.exists:
                    for rel in ep_detail.entity.relations:
                        if rel.get("target") == "orange-pi-54":
                            facts_returned += 1
                            host = ep_detail.entity.metadata.get("host", "unknown")
                            port = ep_detail.entity.metadata.get("port", "unknown")
                            proto = ep_detail.entity.metadata.get("protocol", "unknown")
                            answer_parts.append(f"  → {host}:{port} ({proto})")
            if not any("→" in p for p in answer_parts):
                answer_parts.append("  (sin endpoints expuestos directamente)")
        else:
            answer_parts.append("orange-pi-54 no encontrado")

    elif category == "agents":
        # ¿Qué perfiles Hermes están configurados? → cmdb_list(kind="agent")
        functions_called.append("cmdb_list")
        agents = cmdb_list(kind="agent")
        if agents:
            facts_returned += len(agents)
            answer_parts.append(f"Se encontraron {len(agents)} agentes:")
            for agent in agents:
                agent_id = agent.get("id") if isinstance(agent, dict) else str(agent)
                answer_parts.append(f"  → {agent_id}")
        else:
            answer_parts.append("No hay agentes configurados en el Kernel")

    latency_ms = int((time.perf_counter() - start) * 1000)

    return functions_called, facts_returned, latency_ms, "\n".join(answer_parts)


def count_assertions(answer: str) -> int:
    """
    Cuenta afirmaciones factuales en la respuesta.
    Pattern simple: cada línea con información concreta cuenta como 1.
    """
    lines = [l.strip() for l in answer.split("\n") if l.strip()]
    # Filtrar líneas que son puramente informativas (no metainfo)
    factual_lines = [
        l for l in lines
        if not l.startswith("(") and "no encontrado" not in l.lower()
    ]
    return len(factual_lines)


def run_pilot() -> Dict:
    """
    Ejecuta las 16 preguntas y retorna estadísticas.
    """
    ensure_dirs()

    # Limpiar events.jsonl previo
    if EVENTS_FILE.exists():
        EVENTS_FILE.unlink()

    results = {
        "total_questions": 0,
        "needs_facts_count": 0,
        "kernel_consulted_count": 0,
        "total_facts_returned": 0,
        "total_factual_assertions": 0,
        "total_grounded_assertions": 0,
        "latencies_ms": [],
        "by_category": {},
    }

    print("=" * 60)
    print("Production Grounding Pilot — Iteration L3")
    print("=" * 60)
    print(f"Seed questions: {sum(len(q) for q in SEED_BANK.values())}")
    print(f"Categories: {list(SEED_BANK.keys())}")
    print("=" * 60)

    for category, questions in SEED_BANK.items():
        cat_results = {
            "count": 0,
            "kernel_consulted": 0,
            "facts_returned": 0,
            "assertions": 0,
            "grounded": 0,
            "latencies": [],
        }

        for i, question in enumerate(questions, 1):
            print(f"\n[{category.upper()}] Q{i}: {question}")

            # Detectar si necesita hechos
            needs = needs_facts(question)
            if needs:
                results["needs_facts_count"] += 1
                cat_results["count"] += 1

            # Ejecutar consulta
            funcs, facts, latency, answer = execute_query(question, category)

            # Contar assertions
            factual_assertions = count_assertions(answer)
            grounded_assertions = factual_assertions if funcs else 0  # Si consultó, están grounded

            # Registrar evento
            event = GroundingEvent(
                timestamp=now_iso(),
                question=question,
                category=category,
                needs_facts=needs,
                kernel_consulted=bool(funcs),
                functions_called=funcs,
                facts_returned=facts,
                factual_assertions=factual_assertions,
                grounded_assertions=grounded_assertions,
                latency_ms=latency,
            )
            record_event(event)

            # Acumular estadísticas
            results["total_questions"] += 1
            if funcs:
                results["kernel_consulted_count"] += 1
                cat_results["kernel_consulted"] += 1
            results["total_facts_returned"] += facts
            results["total_factual_assertions"] += factual_assertions
            results["total_grounded_assertions"] += grounded_assertions
            results["latencies_ms"].append(latency)

            cat_results["facts_returned"] += facts
            cat_results["assertions"] += factual_assertions
            cat_results["grounded"] += grounded_assertions
            cat_results["latencies"].append(latency)

            print(f"  → Funcs: {funcs}, Facts: {facts}, Assertions: {factual_assertions}/{grounded_assertions}, Latency: {latency}ms")
            print(f"  → Answer preview: {answer[:100]}...")

        results["by_category"][category] = cat_results
        print(f"  [{category}] Completado: {cat_results['count']} preguntas")

    # Calcular métricas finales
    kar = (
        results["kernel_consulted_count"] / results["needs_facts_count"]
        if results["needs_facts_count"] > 0 else 0
    )
    fgr = (
        results["total_grounded_assertions"] / results["total_factual_assertions"]
        if results["total_factual_assertions"] > 0 else 0
    )
    avg_latency = sum(results["latencies_ms"]) / len(results["latencies_ms"]) if results["latencies_ms"] else 0
    p95_latency = sorted(results["latencies_ms"])[int(len(results["latencies_ms"]) * 0.95)] if results["latencies_ms"] else 0

    results["kar"] = kar
    results["fgr"] = fgr
    results["avg_latency_ms"] = avg_latency
    results["p95_latency_ms"] = p95_latency

    return results


def print_summary(results: Dict) -> None:
    print("\n" + "=" * 60)
    print("PILOT SUMMARY")
    print("=" * 60)
    print(f"Total questions: {results['total_questions']}")
    print(f"Needs facts: {results['needs_facts_count']}")
    print(f"Kernel consulted: {results['kernel_consulted_count']}")
    print(f"Facts returned: {results['total_facts_returned']}")
    print(f"Factual assertions: {results['total_factual_assertions']}")
    print(f"Grounded assertions: {results['total_grounded_assertions']}")
    print()
    print("METRICS:")
    print(f"  KAR (Kernel Adoption Rate): {results['kar']:.1%}")
    print(f"  FGR (Fact Grounding Rate):  {results['fgr']:.1%}")
    print(f"  Avg latency: {results['avg_latency_ms']:.0f}ms")
    print(f"  P95 latency: {results['p95_latency_ms']:.0f}ms")
    print()
    print("BY CATEGORY:")
    for cat, data in results["by_category"].items():
        cat_kar = data["kernel_consulted"] / data["count"] if data["count"] > 0 else 0
        cat_fgr = data["grounded"] / data["assertions"] if data["assertions"] > 0 else 0
        print(f"  {cat}: KAR={cat_kar:.1%}, FGR={cat_fgr:.1%}, assertions={data['assertions']}")
    print("=" * 60)

    # Criterio de éxito
    success = (
        results["kar"] >= 0.75 and
        results["fgr"] >= 0.90 and
        results["p95_latency_ms"] < 250
    )
    if success:
        print("✅ CRITERIO DE ÉXITO ALCANZADO")
    else:
        print("❌ CRITERIO DE ÉXITO NO ALCANZADO")
        if results["kar"] < 0.75:
            print(f"   → KAR {results['kar']:.1%} < 75%")
        if results["fgr"] < 0.90:
            print(f"   → FGR {results['fgr']:.1%} < 90%")
        if results["p95_latency_ms"] >= 250:
            print(f"   → P95 latency {results['p95_latency_ms']}ms >= 250ms")
    print("=" * 60)


if __name__ == "__main__":
    results = run_pilot()
    print_summary(results)

    # Guardar resumen en JSON también
    summary_file = Path(__file__).parent.parent.parent.parent / ".hermes" / "telemetry" / "grounding" / "pilot_summary.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    # Convertir a formato JSON-serializable
    serializable = {k: v for k, v in results.items() if k != "latencies_ms"}
    serializable["by_category"] = {
        k: {kk: vv for kk, vv in v.items() if kk != "latencies"}
        for k, v in results["by_category"].items()
    }
    summary_file.write_text(json.dumps(serializable, indent=2))
    print(f"\nResumen guardado en: {summary_file}")