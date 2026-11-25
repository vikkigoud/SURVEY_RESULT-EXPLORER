def filter_records(records, query="", category="All", start_date="", end_date=""):
    q = query.strip().lower()
    result = []
    for r in records:
        if category != "All" and r.category != category: continue
        if start_date and r.response_date < start_date: continue
        if end_date and r.response_date > end_date: continue
        if q and q not in " ".join([r.respondent, r.category, r.comments, str(r.rating), r.response_date]).lower(): continue
        result.append(r)
    return result
