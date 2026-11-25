import csv, json
from pathlib import Path
from .analytics import summarize, insights


def export_records(records, path, fmt=None):
    path = Path(path); fmt = (fmt or path.suffix.lstrip(".")).lower()
    rows = [r.to_dict() for r in records]
    if fmt == "csv":
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["id","respondent","category","rating","response_date","comments"])
            writer.writeheader(); writer.writerows(rows)
    elif fmt == "json":
        path.write_text(json.dumps({"records": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    else: raise ValueError("Supported record export formats: CSV and JSON")


def export_summary(records, path, fmt):
    s = summarize(records); ins = insights(records)
    fmt = fmt.lower()
    if fmt == "md":
        text = "# Survey Result Explorer Summary\n\n" + f"- Total responses: {s['total']}\n- Average rating: {s['average']}\n- High (80+): {s['high']}\n- Low (<50): {s['low']}\n\n## Category counts\n" + "\n".join(f"- {k}: {v}" for k,v in s["categories"].items()) + "\n\n## Insights\n" + "\n".join(f"- {x}" for x in ins) + "\n"
    elif fmt == "txt":
        text = "SURVEY RESULT EXPLORER SUMMARY\n" + f"Total responses: {s['total']}\nAverage rating: {s['average']}\nHigh (80+): {s['high']}\nLow (<50): {s['low']}\n\nCategory counts:\n" + "\n".join(f"{k}: {v}" for k,v in s["categories"].items()) + "\n\nInsights:\n" + "\n".join(ins) + "\n"
    else: raise ValueError("Supported summary formats: MD and TXT")
    Path(path).write_text(text, encoding="utf-8")
