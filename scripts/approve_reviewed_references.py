"""Explicitly add staff-approved references; never use a generated draft as ground truth."""
import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path


def approved_rows(rows, snapshot):
    result = []
    for row in rows:
        if row.get('review_status', '').strip().lower() != 'approved':
            continue
        for name in ['question', 'reviewer', 'reviewed_date', 'expected_answer', 'relevant_context']:
            if not row.get(name, '').strip():
                raise ValueError(f"{row.get('case_id')}: approved row requires {name}")
        date.fromisoformat(row['reviewed_date'].strip())
        if row.get('index_snapshot_sha256') != snapshot:
            raise ValueError('The index changed since review; recheck the policy and sources before approval')
        result.append({name: row[name].strip() for name in
                       ['question', 'expected_answer', 'relevant_context', 'reviewer', 'reviewed_date', 'index_snapshot_sha256']})
    if not result:
        raise ValueError('No fully staff-approved rows. Pending rows are never promoted automatically.')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reviewed-csv', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    snapshot = hashlib.sha256((root / 'backend_files/faiss_index/index.pkl').read_bytes()).hexdigest()
    with args.reviewed_csv.open(newline='', encoding='utf-8-sig') as stream:
        approved = approved_rows(list(csv.DictReader(stream)), snapshot)
    path = root / 'backend_files/reference_catalog.json'
    catalog = json.loads(path.read_text())
    existing = {' '.join(item['question'].split()).casefold(): item for item in catalog}
    for item in approved:
        key = ' '.join(item['question'].split()).casefold()
        if key in existing:
            raise ValueError('Question already exists; review catalog changes explicitly rather than silently replacing it')
        existing[key] = item
    backup = path.with_name('reference_catalog.before_staff_review.json')
    if backup.exists():
        raise ValueError('A review backup already exists. Preserve/review the earlier change before another promotion.')
    backup.write_text(path.read_text())
    path.write_text(json.dumps(list(existing.values()), indent=2))
    print(f'Added {len(approved)} staff-approved judge-only references. Original catalog preserved in {backup.name}.')


if __name__ == '__main__':
    main()
