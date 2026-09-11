import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "items.json"


def load_items(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load item records from local JSON database."""
    target_path = filepath or DATA_PATH
    if not target_path.exists():
        return []
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)


def sanitize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove protected fields like verification_feature before returning data to frontend.
    """
    clean_item = dict(item)
    clean_item.pop("verification_feature", None)
    return clean_item


def get_raw_item_by_id(item_id: str, filepath: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Retrieve full un-sanitized item record including verification_feature."""
    items = load_items(filepath)
    for item in items:
        if item.get("id") == item_id:
            return item
    return None


def search_items(
    extracted_criteria: Dict[str, Any],
    filepath: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Search database items matching extracted criteria.
    Returns sanitized candidate items that match the search criteria.
    """
    raw_items = load_items(filepath)
    if not raw_items:
        return []

    # Extract search criteria
    category = extracted_criteria.get("category", "") or ""
    brand = extracted_criteria.get("brand", "") or ""
    color = extracted_criteria.get("color", "") or ""
    location = extracted_criteria.get("location", "") or ""

    category = category.lower().strip()
    brand = brand.lower().strip()
    color = color.lower().strip()
    location = location.lower().strip()

    candidates = []
    for item in raw_items:
        # Calculate match score for this item
        match_score = 0
        max_score = 0

        # Category match (highest priority)
        if category:
            max_score += 3
            item_category = item.get("category", "").lower().strip()
            if category in item_category or item_category in category:
                match_score += 3

        # Brand match
        if brand:
            max_score += 2
            item_brand = item.get("brand", "").lower().strip()
            if brand in item_brand or item_brand in brand:
                match_score += 2

        # Color match
        if color:
            max_score += 2
            item_color = item.get("color", "").lower().strip()
            if color in item_color or item_color in color:
                match_score += 2

        # Location match
        if location:
            max_score += 2
            item_location = item.get("location", "").lower().strip()
            if location in item_location or item_location in location:
                match_score += 2

        # If no criteria provided, include all items with low score
        if max_score == 0:
            match_score = 1
            max_score = 1

        # Only include items that have at least some match
        if match_score > 0:
            sanitized = sanitize_item(item)
            sanitized["match_score"] = match_score / max_score if max_score > 0 else 0
            candidates.append(sanitized)

    # Sort by match score (descending)
    candidates.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    return candidates
