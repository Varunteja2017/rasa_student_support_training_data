import json
import yaml
from pathlib import Path

base = Path(__file__).resolve().parents[1]
intent_report = base / 'results' / 'intent_report.json'
domain_file = base / 'domain.yml'

with open(intent_report, 'r', encoding='utf-8') as f:
    data = json.load(f)

# filter out summary keys
ignore = {'accuracy', 'macro avg', 'weighted avg', 'micro avg'}
intents_in_report = [k for k in data.keys() if k not in ignore]

with open(domain_file, 'r', encoding='utf-8') as f:
    dom = yaml.safe_load(f)

existing_intents = set(dom.get('intents', []))
missing = [i for i in intents_in_report if i not in existing_intents]

print('MISSING_INTENTS_COUNT:', len(missing))
for m in missing:
    print(m)
