from collections import Counter, defaultdict
from statistics import mean
from datetime import datetime


def summarize(records):
    if not records:
        return {"total": 0, "average": 0, "categories": {}, "high": 0, "low": 0, "trend": {}, "valid_percent": 100}
    vals = [float(r.rating) for r in records]
    cats = Counter(r.category for r in records)
    by_month = defaultdict(list)
    for r in records:
        try: by_month[datetime.strptime(r.response_date, "%Y-%m-%d").strftime("%Y-%m")].append(float(r.rating))
        except (ValueError, TypeError): pass
    return {"total": len(records), "average": round(mean(vals), 2), "categories": dict(cats),
            "high": sum(v >= 80 for v in vals), "low": sum(v < 50 for v in vals),
            "trend": {k: round(mean(v), 2) for k, v in sorted(by_month.items())},
            "valid_percent": 100}


def insights(records):
    s = summarize(records)
    if not records: return ["Add survey responses to see insights."]
    cat_ratings = defaultdict(list)
    for r in records: cat_ratings[r.category].append(float(r.rating))
    ordered = sorted((k, round(sum(v)/len(v), 2)) for k, v in cat_ratings.items())
    out = [f"Dataset contains {s['total']} response(s) across {len(s['categories'])} category/categories.",
           f"Overall average rating is {s['average']:.2f} out of 100.",
           f"{s['high']} response(s) are high (80+) and {s['low']} are low (<50)."]
    if ordered: out += [f"Highest average category: {ordered[-1][0]} ({ordered[-1][1]}).", f"Lowest average category: {ordered[0][0]} ({ordered[0][1]})."]
    return out
