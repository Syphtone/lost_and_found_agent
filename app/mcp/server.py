"""FastMCP tool server for the Lost & Found Agent.

Exposes the service layer as real MCP tools. Each tool is a thin, well-typed
wrapper over app.services.items — no business logic or SQL lives here, so the
same functions back both the MCP interface and any direct callers.

Tools:
  * create_lost_report      — register a lost-item report
  * create_found_report     — register a found-item report
  * search_items            — semantic search across reports (pgvector RAG)
  * find_potential_matches  — candidate matches of the opposite kind
  * get_item                — fetch one report by id

Run standalone:  python -m app.mcp.server
"""

from __future__ import annotations

from typing import Any, Optional

from fastmcp import FastMCP

from app.config import settings
from app.services import items as items_service

mcp = FastMCP("lost-and-found")


@mcp.tool
def create_lost_report(
    raw_text: str,
    item_type: Optional[str] = None,
    color: Optional[str] = None,
    brand: Optional[str] = None,
    location: Optional[str] = None,
    reported_date: Optional[str] = None,
) -> dict[str, Any]:
    """Register a LOST-item report and store its embedding for retrieval.

    raw_text is the user's free-text description; the structured fields are
    optional extracted attributes. Returns the created report row.
    """
    return items_service.create_report(
        "lost",
        raw_text,
        item_type=item_type,
        color=color,
        brand=brand,
        location=location,
        reported_date=reported_date,
    )


@mcp.tool
def create_found_report(
    raw_text: str,
    item_type: Optional[str] = None,
    color: Optional[str] = None,
    brand: Optional[str] = None,
    location: Optional[str] = None,
    reported_date: Optional[str] = None,
) -> dict[str, Any]:
    """Register a FOUND-item report and store its embedding for retrieval."""
    return items_service.create_report(
        "found",
        raw_text,
        item_type=item_type,
        color=color,
        brand=brand,
        location=location,
        reported_date=reported_date,
    )


@mcp.tool
def search_items(
    query_text: str,
    kind: Optional[str] = None,
    top_k: int = settings.retrieval_top_k,
) -> list[dict[str, Any]]:
    """Semantic search over reports via pgvector cosine similarity.

    Optionally filter by kind ('lost' or 'found'). Each result carries a
    `similarity` score in [0, 1].
    """
    return items_service.search_items(query_text, kind=kind, top_k=top_k)


@mcp.tool
def find_potential_matches(
    item_id: Optional[int] = None,
    query_text: Optional[str] = None,
    top_k: int = settings.retrieval_top_k,
) -> dict[str, Any]:
    """Find candidate matches of the OPPOSITE kind for a report or a query.

    Provide either `item_id` (an existing report) or `query_text` (a free-text
    lost-item description). Returns the query, the target kind, and ranked
    candidates with similarity scores.
    """
    return items_service.find_potential_matches(
        item_id=item_id, query_text=query_text, top_k=top_k
    )


@mcp.tool
def get_item(item_id: int) -> Optional[dict[str, Any]]:
    """Fetch a single report by id, or null if it does not exist."""
    return items_service.get_item(item_id)


if __name__ == "__main__":
    # Default stdio transport; the agent connects as an MCP client.
    mcp.run()
