"""Service layer: report storage and semantic retrieval (RAG core).

These functions are the real operations the rest of the system composes:
  * MCP tools (app/mcp/server.py) are thin wrappers over these.
  * The agent's retrieval node ultimately reaches the database through here.

All embedding and SQL live in this layer, so tools and agent code never touch
psycopg or pgvector directly. Similarity queries cast the query vector with
`::vector`, which pgvector requires when the vector is passed as a parameter.
"""

from __future__ import annotations

from typing import Any, Optional

from app.db import get_connection
from app.embeddings import embed_text

# Columns returned to callers (embedding is intentionally omitted — large and
# not useful downstream).
_RETURN_COLUMNS = (
    "id, kind, status, item_type, color, brand, location, "
    "reported_date, raw_text, created_at"
)

OPPOSITE_KIND = {"lost": "found", "found": "lost"}


def _row_to_dict(columns: list[str], row: tuple) -> dict[str, Any]:
    return dict(zip(columns, row))


def create_report(
    kind: str,
    raw_text: str,
    *,
    item_type: Optional[str] = None,
    color: Optional[str] = None,
    brand: Optional[str] = None,
    location: Optional[str] = None,
    reported_date: Optional[str] = None,
) -> dict[str, Any]:
    """Create a lost/found report: embed `raw_text` and insert the row.

    Returns the created row as a dict (without the embedding).
    """
    if kind not in ("lost", "found"):
        raise ValueError(f"kind must be 'lost' or 'found', got {kind!r}")

    embedding = embed_text(raw_text)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO items
                    (kind, item_type, color, brand, location, reported_date,
                     raw_text, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING {_RETURN_COLUMNS}
                """,
                (kind, item_type, color, brand, location, reported_date,
                 raw_text, embedding),
            )
            columns = [c.name for c in cur.description]
            return _row_to_dict(columns, cur.fetchone())


def get_item(item_id: int) -> Optional[dict[str, Any]]:
    """Fetch a single report by id, or None if it does not exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {_RETURN_COLUMNS} FROM items WHERE id = %s",
                (item_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            columns = [c.name for c in cur.description]
            return _row_to_dict(columns, row)


def search_items(
    query_text: str,
    *,
    kind: Optional[str] = None,
    top_k: int = 5,
    only_open: bool = True,
) -> list[dict[str, Any]]:
    """Semantic search over reports via pgvector cosine similarity.

    Embeds `query_text`, then returns the top_k nearest rows (optionally
    filtered by `kind` and to `status = 'open'`). Each result includes a
    `similarity` score in [0, 1] (1 - cosine distance).
    """
    embedding = embed_text(query_text)

    filters = []
    params: list[Any] = [embedding]  # for the SELECT similarity expression
    if kind is not None:
        filters.append("kind = %s")
        params.append(kind)
    if only_open:
        filters.append("status = 'open'")
    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    params.append(embedding)  # for the ORDER BY distance expression
    params.append(top_k)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {_RETURN_COLUMNS},
                       1 - (embedding <=> %s::vector) AS similarity
                FROM items
                {where}
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                tuple(params),
            )
            columns = [c.name for c in cur.description]
            return [_row_to_dict(columns, row) for row in cur.fetchall()]


def find_potential_matches(
    *,
    item_id: Optional[int] = None,
    query_text: Optional[str] = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """Find candidate matches of the OPPOSITE kind for a report or query.

    Provide either `item_id` (matches against that stored report's kind) or
    `query_text` (treated as a lost-item description searching found items).
    Returns {"query": ..., "target_kind": ..., "candidates": [...]}.
    """
    if item_id is not None:
        source = get_item(item_id)
        if source is None:
            raise ValueError(f"item {item_id} not found")
        text = source["raw_text"]
        target_kind = OPPOSITE_KIND[source["kind"]]
    elif query_text is not None:
        text = query_text
        target_kind = "found"  # a lost-item query looks for found items
    else:
        raise ValueError("provide either item_id or query_text")

    candidates = search_items(text, kind=target_kind, top_k=top_k, only_open=True)
    return {
        "query": text,
        "target_kind": target_kind,
        "candidates": candidates,
    }
