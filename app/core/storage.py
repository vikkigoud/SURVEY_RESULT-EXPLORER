import csv, json, shutil
from pathlib import Path
from datetime import datetime
from .models import SurveyRecord
from .validation import validate_record, ValidationError


class Storage:
    FIELDS = ["id", "respondent", "category", "rating", "response_date", "comments"]
    def __init__(self, base_dir):
        self.base = Path(base_dir)
        self.data_dir = self.base / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "backups").mkdir(exist_ok=True)
        self.csv_path = self.data_dir / "surveys.csv"
        self.json_path = self.data_dir / "surveys.json"
        self.audit_path = self.data_dir / "audit.log"

    def load(self):
        if self.json_path.exists():
            try:
                payload = json.loads(self.json_path.read_text(encoding="utf-8"))
                rows = payload.get("records", payload) if isinstance(payload, dict) else payload
                records = []
                for row in rows:
                    values = validate_record(row.get("respondent", ""), row.get("category", ""), row.get("rating", ""), row.get("response_date", ""), row.get("comments", ""))
                    records.append(SurveyRecord(**{**{k: row.get(k, "") for k in self.FIELDS}, "rating": values[2]}))
                return records
            except (json.JSONDecodeError, TypeError, KeyError, AttributeError, ValidationError, ValueError):
                pass
        if self.csv_path.exists():
            try:
                with self.csv_path.open(newline="", encoding="utf-8-sig") as f:
                    records = []
                    for row in csv.DictReader(f):
                        values = validate_record(row.get("respondent", ""), row.get("category", ""), row.get("rating", ""), row.get("response_date", ""), row.get("comments", ""))
                        records.append(SurveyRecord(**{**{k: row.get(k, "") for k in self.FIELDS}, "rating": values[2]}))
                    return records
            except (csv.Error, OSError, ValidationError, ValueError):
                pass
        return []

    def save(self, records):
        if self.json_path.exists() and self.json_path.stat().st_size:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = self.data_dir / "backups" / f"surveys_{stamp}.json"
            try:
                shutil.copy2(self.json_path, backup)
            except OSError:
                pass
        payload = {"schema_version": 1, "updated_at": datetime.now().isoformat(timespec="seconds"),
                  "records": [r.to_dict() for r in records]}
        self.json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        with self.csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDS)
            writer.writeheader()
            writer.writerows(r.to_dict() for r in records)

    def log(self, action, details=""):
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {action}: {details}\n")
