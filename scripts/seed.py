"""Seed the database with sample FOUND reports for the demo.

Loads a small, varied corpus so the agent has something to match against:
  * a strong match for the canonical "black Sony headphones near the library",
  * near-neighbours that make matching non-trivial, and
  * unrelated items.

Usage:
    python -m scripts.seed          # insert sample found reports
    python -m scripts.seed --reset  # delete ALL items first, then insert
"""

from __future__ import annotations

import sys

from app.db import run
from app.services.items import create_report

SAMPLE_FOUND = [
    {
        "raw_text": "Found black Sony over-ear headphones near the library entrance",
        "item_type": "headphones", "color": "black", "brand": "Sony", "location": "library",
    },
    {
        "raw_text": "Found a pair of white Apple earbuds in the library reading room",
        "item_type": "earbuds", "color": "white", "brand": "Apple", "location": "library",
    },
    {
        "raw_text": "Found black wireless headphones in the student cafeteria",
        "item_type": "headphones", "color": "black", "brand": None, "location": "cafeteria",
    },
    {
        "raw_text": "Found a blue umbrella at the main gate",
        "item_type": "umbrella", "color": "blue", "brand": None, "location": "main gate",
    },
    {
        "raw_text": "Found a brown leather wallet near the parking lot",
        "item_type": "wallet", "color": "brown", "brand": None, "location": "parking lot",
    },
    {
        "raw_text": "Found a silver MacBook charger in lecture hall B",
        "item_type": "charger", "color": "silver", "brand": "Apple", "location": "lecture hall B",
    },
]


def reset() -> None:
    run("DELETE FROM items")
    print("Deleted all existing items.")


def seed() -> None:
    created = []
    for item in SAMPLE_FOUND:
        row = create_report("found", item["raw_text"],
                            item_type=item["item_type"], color=item["color"],
                            brand=item["brand"], location=item["location"])
        created.append(row["id"])
        print(f"  [{row['id']}] {row['raw_text']}")
    print(f"Seeded {len(created)} found reports.")


if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset()
    seed()
