"""Evaluation runner for the Lost & Found agent.

Loads eval/dataset.json, runs each query through the real agent pipeline, and
compares the actual routing decision to the expected one. Prints a per-case
table and overall decision accuracy.

Prerequisites: the corpus must be seeded first:
    python -m scripts.seed --reset
Then:
    python -m eval.run_eval
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.agent.graph import run_agent

DATASET_PATH = Path(__file__).with_name("dataset.json")


async def evaluate() -> float:
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    cases = data["cases"]

    print(f"Running {len(cases)} evaluation cases...\n")
    header = f"{'id':<28} {'expected':<10} {'actual':<10} {'conf':>6}  result"
    print(header)
    print("-" * len(header))

    passed = 0
    for case in cases:
        state = await run_agent(case["query"], kind="lost")
        actual = state.get("decision", "no_match")
        conf = state.get("confidence", 0.0)
        ok = actual == case["expected_decision"]
        passed += ok
        mark = "PASS" if ok else "FAIL"
        print(f"{case['id']:<28} {case['expected_decision']:<10} {actual:<10} {conf:>6.3f}  {mark}")

    accuracy = passed / len(cases) if cases else 0.0
    print("-" * len(header))
    print(f"\nDecision accuracy: {passed}/{len(cases)} = {accuracy:.0%}")
    return accuracy


if __name__ == "__main__":
    asyncio.run(evaluate())
