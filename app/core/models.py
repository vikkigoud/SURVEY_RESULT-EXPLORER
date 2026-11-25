from dataclasses import dataclass, asdict
from datetime import date
from typing import Optional
import uuid

@dataclass
class SurveyRecord:
    id: str
    respondent: str
    category: str
    rating: float
    response_date: str
    comments: str = ""

    @classmethod
    def create(cls, respondent, category, rating, response_date=None, comments=""):
        return cls(str(uuid.uuid4())[:8], respondent.strip(), category.strip(), float(rating),
                   response_date or date.today().isoformat(), comments.strip())

    def to_dict(self):
        return asdict(self)
