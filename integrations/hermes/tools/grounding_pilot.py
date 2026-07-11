# grounding_pilot.py — Production Grounding Pilot — Iteration L3
#
# Granularity mínima: medir si un agente REAL consulta el Kernel cuando necesita hechos.
#
# No mide: calidad del modelo, razonamiento, prompts.
# Sí mide: consultas al Kernel, funciones invocadas, hechos retornados, afirmaciones fundamentadas.

import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List

# Constantes del piloto
TELEMETRY_DIR = Path.home() / ".hermes" / "telemetry" / "grounding"
EVENTS_FILE = TELEMETRY_DIR / "events.jsonl"
QUESTIONS_FILE = TELEMETRY_DIR / "questions.json"


@dataclass
class GroundingEvent:
    """Un evento = una pregunta → una decisión del agente."""

    timestamp: str
    question: str
    category: str
    needs_facts: bool
    kernel_consulted: bool
    functions_called: List[str] = field(default_factory=list)
    facts_returned: int = 0
    factual_assertions: int = 0
    grounded_assertions: int = 0
    latency_ms: int = 0

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


# Banco de preguntas semilla — 16 preguntas, 4 categorías, 4 repeticiones
SEED_BANK = {
    "infrastructure": [
        "¿Dónde corre Ollama?",
        "¿Dónde corre Ollama?",
        "¿Dónde corre Ollama?",
        "¿Dónde corre Ollama?",
    ],
    "dependencies": [
        "¿Qué depende de MySQL?",
        "¿Qué depende de MySQL?",
        "¿Qué depende de MySQL?",
        "¿Qué depende de MySQL?",
    ],
    "endpoints": [
        "¿Qué puertos expone orange-pi-54?",
        "¿Qué puertos expone orange-pi-54?",
        "¿Qué puertos expone orange-pi-54?",
        "¿Qué puertos expone orange-pi-54?",
    ],
    "agents": [
        "¿Qué perfiles Hermes están configurados?",
        "¿Qué perfiles Hermes están configurados?",
        "¿Qué perfiles Hermes están configurados?",
        "¿Qué perfiles Hermes están configurados?",
    ],
}


def ensure_dirs() -> None:
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)


def save_questions() -> None:
    """Persiste el banco de preguntas en disco (idempotente)."""
    ensure_dirs()
    if not QUESTIONS_FILE.exists():
        QUESTIONS_FILE.write_text(
            json.dumps(SEED_BANK, indent=2, ensure_ascii=False)
        )


def record_event(event: GroundingEvent) -> None:
    """Append un evento a events.jsonl."""
    ensure_dirs()
    with EVENTS_FILE.open("a") as f:
        f.write(event.to_jsonl() + "\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    save_questions()
    print(f"Telemetry dir: {TELEMETRY_DIR}")
    print(f"Questions file: {QUESTIONS_FILE}")
    print(f"Events file: {EVENTS_FILE}")
    print(f"Total seed questions: {sum(len(q) for q in SEED_BANK.values())}")