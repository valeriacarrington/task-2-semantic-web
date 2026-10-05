import csv
import io
import json
import re
from datetime import datetime, timezone

import requests

URL = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "mkr1/1.0", "Accept": "text/csv"}


def run(query):
    r = requests.get(URL, params={"query": query}, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.text


def rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def save(name, text):
    with open(name, "w", encoding="utf-8", newline="") as f:
        f.write(text)


results = {}
note = None

for n in (1, 2, 3):
    with open(f"q{n}.rq", encoding="utf-8") as f:
        query = f.read()
    text = run(query)

    # Q1: якщо менше 5 рядків — зменшуємо поріг удвічі
    if n == 1 and len(rows(text)) < 5:
        m = re.search(r"(\?value\s*>\s*)(\d+(?:\.\d+)?)", query)
        new = float(m.group(2)) / 2
        new = int(new) if new.is_integer() else new
        query = query[:m.start()] + f"{m.group(1)}{new}" + query[m.end():]
        save("q1.rq", query)
        text = run(query)
        note = f"Примітка: Q1 повернув менше 5 рядків, поріг зменшено до {new}."

    save(f"q{n}.csv", text)
    results[n] = rows(text)

with open("meta.json", "w", encoding="utf-8") as f:
    json.dump({"retrieved_at": datetime.now(timezone.utc).isoformat()}, f)

r1, r2, r3 = results[1][0], results[2][0], results[3][0]
lines = [
    f"Q1: {r1['itemLabel']} — {r1['value']}",
    f"Q2: {r2['regionLabel']} — {r2['cnt']}",
    f"Q3: {r3['population']}",
]
if note:
    lines.append(note)

with open("ANSWERS.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")