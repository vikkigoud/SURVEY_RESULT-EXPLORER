import unittest, tempfile
from pathlib import Path
from app.core.models import SurveyRecord
from app.core.validation import validate_record, ValidationError
from app.core.cleaning import clean_records
from app.core.analytics import summarize
from app.core.search import filter_records
from app.core.storage import Storage

class CoreTests(unittest.TestCase):
    def test_validation_rating_bounds(self):
        self.assertEqual(validate_record("A","B",100,"2026-01-01")[2],100)
        with self.assertRaises(ValidationError): validate_record("A","B",101,"2026-01-01")
        with self.assertRaises(ValidationError): validate_record("","B",50,"2026-01-01")
    def test_clean_duplicates(self):
        a=SurveyRecord.create("A","Course",88,"2026-01-01")
        b=SurveyRecord.create("a","course",90,"2026-01-01")
        cleaned,report=clean_records([a,b]); self.assertEqual(len(cleaned),1); self.assertEqual(report["duplicates_removed"],1)
    def test_analytics_and_filter(self):
        rows=[SurveyRecord.create("A","Course",80,"2026-01-01"),SurveyRecord.create("B","Food",60,"2026-01-02")]
        s=summarize(rows); self.assertEqual(s["total"],2); self.assertEqual(s["average"],70)
        self.assertEqual(len(filter_records(rows,category="Food")),1)
    def test_storage_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            store=Storage(d); rows=[SurveyRecord.create("Test","Category",92,"2026-02-01","Notes")]; store.save(rows); loaded=store.load(); self.assertEqual(loaded[0].respondent,"Test"); self.assertEqual(float(loaded[0].rating),92)
if __name__=="__main__": unittest.main()
