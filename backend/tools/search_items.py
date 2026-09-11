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
    Returns sanitized candidate items.
    """
    raw_items = load_items(filepath)
    if not raw_items:
        return []

    # If no specific search parameters are provided, return all items sanitized
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
        sanitized = sanitize_item(item)
        candidates.append(sanitized)

    return candidates
