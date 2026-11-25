from datetime import date


class ValidationError(ValueError):
    pass


def validate_record(respondent, category, rating, response_date, comments=""):
    respondent = str(respondent).strip()
    category = str(category).strip()
    comments = str(comments).strip()
    if not respondent:
        raise ValidationError("Respondent name/ID is required.")
    if len(respondent) > 100:
        raise ValidationError("Respondent field must be 100 characters or fewer.")
    if not category:
        raise ValidationError("Category is required.")
    if len(category) > 60:
        raise ValidationError("Category must be 60 characters or fewer.")
    try:
        rating = float(rating)
    except (TypeError, ValueError):
        raise ValidationError("Rating must be a number from 0 to 100.")
    if not 0 <= rating <= 100:
        raise ValidationError("Rating must be between 0 and 100.")
    try:
        date.fromisoformat(str(response_date))
    except (TypeError, ValueError):
        raise ValidationError("Date must be valid and formatted YYYY-MM-DD.")
    if len(comments) > 1000:
        raise ValidationError("Comments must be 1000 characters or fewer.")
    return respondent, category, rating, str(response_date), comments
