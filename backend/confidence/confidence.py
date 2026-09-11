from typing import Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class ConfidenceConfig:
    # Feature weights (must sum to 1.0)
    WEIGHT_SIMILARITY: float = 0.40
    WEIGHT_LOCATION: float = 0.20
    WEIGHT_TIME: float = 0.15
    WEIGHT_CATEGORY: float = 0.15
    WEIGHT_BRAND: float = 0.10

    # Confidence Thresholds
    HIGH_THRESHOLD: float = 0.85
    MEDIUM_THRESHOLD: float = 0.60


DEFAULT_CONFIG = ConfidenceConfig()


def calculate_similarity(user_query: str, item_desc: str) -> float:
    """Calculate basic text semantic/keyword similarity (0.0 to 1.0)."""
    if not user_query or not item_desc:
        return 0.0

    user_words = set(user_query.lower().split())
    item_words = set(item_desc.lower().split())

    # Ignore trivial stopwords
    stopwords = {
        "i", "my", "the", "a", "an", "in", "at", "near", "lost", "misplaced", "around",
        "with", "on", "of", "and", "or", "for", "to", "from", "by", "about", "it", "is",
        "was", "were", "are", "have", "has", "had", "some", "someone", "something"
    }
    user_words -= stopwords
    item_words -= stopwords

    if not user_words or not item_words:
        return 0.0

    intersection = user_words.intersection(item_words)
    union = user_words.union(item_words)

    # Jaccard index + substring bonus
    jaccard = len(intersection) / len(union) if union else 0.0

    # Substring check bonus
    matching_user_words = sum(1 for w in user_words if w in item_desc.lower())
    substring_score = matching_user_words / len(user_words) if user_words else 0.0

    return max(jaccard, substring_score)


def calculate_field_match(val1: str, val2: str) -> float:
    """Calculate match score between two strings (0.0 to 1.0)."""
    if not val1:
        # If user didn't specify this field (e.g. time), do not penalize matching items
        return 1.0
    if not val2:
        return 0.5

    v1, v2 = val1.lower().strip(), val2.lower().strip()
    if v1 == v2:
        return 1.0
    if v1 in v2 or v2 in v1:
        return 0.85
    return 0.0


def calculate_confidence(
    extracted: Dict[str, Any],
    candidate_item: Dict[str, Any],
    user_message: str = "",
    config: ConfidenceConfig = DEFAULT_CONFIG
) -> Tuple[float, str]:
    """
    Calculate confidence score and confidence level for a candidate item.
    
    Returns:
        (confidence_score: float, confidence_level: "HIGH" | "MEDIUM" | "LOW")
    """
    # 1. Similarity (combining item description, category, brand, color, location)
    item_full_text = f"{candidate_item.get('description', '')} {candidate_item.get('category', '')} {candidate_item.get('brand', '')} {candidate_item.get('color', '')} {candidate_item.get('location', '')}"
    similarity = calculate_similarity(user_message, item_full_text)

    # 2. Location match
    user_loc = extracted.get("location", "")
    item_loc = candidate_item.get("location", "")
    location_match = calculate_field_match(user_loc, item_loc)

    # 3. Time match
    user_time = extracted.get("time", "")
    item_time = candidate_item.get("found_time", "")
    time_match = calculate_field_match(user_time, item_time)

    # 4. Category match
    user_cat = extracted.get("category", "")
    item_cat = candidate_item.get("category", "")
    category_match = calculate_field_match(user_cat, item_cat)

    # 5. Brand match
    user_brand = extracted.get("brand", "")
    item_brand = candidate_item.get("brand", "")
    brand_match = calculate_field_match(user_brand, item_brand)

    # Calculate weighted score
    final_score = (
        config.WEIGHT_SIMILARITY * similarity +
        config.WEIGHT_LOCATION * location_match +
        config.WEIGHT_TIME * time_match +
        config.WEIGHT_CATEGORY * category_match +
        config.WEIGHT_BRAND * brand_match
    )

    # If semantic/keyword similarity is very low (< 0.15), cap confidence score to low
    if similarity < 0.15:
        final_score = min(final_score, 0.40)

    final_score = round(min(max(final_score, 0.0), 1.0), 2)

    # Determine confidence level
    if final_score >= config.HIGH_THRESHOLD:
        confidence_level = "HIGH"
    elif final_score >= config.MEDIUM_THRESHOLD:
        confidence_level = "MEDIUM"
    else:
        confidence_level = "LOW"

    return final_score, confidence_level
