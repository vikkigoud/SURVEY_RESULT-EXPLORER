from collections import Counter
from dataclasses import replace
from .validation import validate_record, ValidationError


def clean_records(records):
    """Trim text, validate entries, and remove duplicate rows by respondent/category/date."""
    cleaned, errors, removed = [], [], 0
    seen = set()
    for idx, row in enumerate(records, 1):
        try:
            values = validate_record(row.respondent, row.category, row.rating, row.response_date, row.comments)
            key = (values[0].casefold(), values[1].casefold(), values[3])
            if key in seen:
                removed += 1
                continue
            seen.add(key)
            cleaned.append(replace(row, respondent=values[0], category=values[1], rating=values[2], response_date=values[3], comments=values[4]))
        except ValidationError as exc:
            errors.append({"row": idx, "id": row.id, "error": str(exc)})
    return cleaned, {"original": len(records), "cleaned": len(cleaned), "duplicates_removed": removed, "invalid": errors}
