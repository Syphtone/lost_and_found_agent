import os
from typing import List, Dict, Any, Optional

# PostgreSQL connection string from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/lost_found_db")


def sanitize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize item payload to protect verification_feature."""
    clean = dict(item)
    clean.pop("verification_feature", None)
    clean.pop("embedding", None)
    return clean


def search_items_postgres(
    extracted_criteria: Dict[str, Any],
    query_embedding: Optional[List[float]] = None
) -> List[Dict[str, Any]]:
    """
    Search items in PostgreSQL database.
    Supports pgvector similarity if query_embedding is provided,
    otherwise filters by category, brand, color, location using SQL.
    """
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        # Fallback message if psycopg2 is not installed in the environment
        raise RuntimeError("psycopg2 is not installed. Install psycopg2-binary to use PostgreSQL integration.")

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            category = extracted_criteria.get("category")
            brand = extracted_criteria.get("brand")
            color = extracted_criteria.get("color")
            location = extracted_criteria.get("location")

            # Vector Search (RAG / pgvector) if embedding is provided
            if query_embedding and len(query_embedding) > 0:
                vector_str = "[" + ",".join(map(str, query_embedding)) + "]"
                sql = """
                    SELECT id, category, brand, color, location, found_time, description, verification_feature,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM items
                    WHERE status = 'unclaimed'
                    ORDER BY embedding <=> %s::vector ASC
                    LIMIT 10;
                """
                cur.execute(sql, (vector_str, vector_str))
                rows = cur.fetchall()
            else:
                # SQL Attribute Search
                conditions = ["status = 'unclaimed'"]
                params = []

                if category:
                    conditions.append("LOWER(category) LIKE %s")
                    params.append(f"%{category.lower()}%")
                if brand:
                    conditions.append("LOWER(brand) LIKE %s")
                    params.append(f"%{brand.lower()}%")
                if color:
                    conditions.append("LOWER(color) LIKE %s")
                    params.append(f"%{color.lower()}%")
                if location:
                    conditions.append("LOWER(location) LIKE %s")
                    params.append(f"%{location.lower()}%")

                where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
                sql = f"""
                    SELECT id, category, brand, color, location, found_time, description, verification_feature
                    FROM items
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT 20;
                """
                cur.execute(sql, tuple(params))
                rows = cur.fetchall()

            candidates = [sanitize_item(dict(row)) for row in rows]
            return candidates
    finally:
        conn.close()


def get_raw_item_by_id_postgres(item_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full un-sanitized item record from PostgreSQL database including verification_feature."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        return None

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM items WHERE id = %s;", (item_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()
