from pathlib import Path
import re

p = Path(__file__).resolve().parents[1] / 'nlu.yml'
text = p.read_text(encoding='utf-8')
lines = text.splitlines()
start = None
for idx, line in enumerate(lines, start=1):
    if re.match(r"\s*-\s*intent:\s*ask_admission_documents\b", line):
        start = idx
        break
if not start:
    print('ask_admission_documents intent not found')
    raise SystemExit(0)
# find examples: |
for i in range(start, start+20):
    if i-1 < len(lines) and re.match(r"\s*examples:\s*\|", lines[i-1]):
        ex_start = i+0
        break
else:
    print('examples block not found near intent')
    raise SystemExit(0)
# print subsequent lines until next intent or blank gap
print(f'Printing lines around intent (from line {start}):')
for j in range(ex_start, ex_start+50):
    if j-1 >= len(lines):
        break
    l = lines[j-1]
    # stop if next intent
    if re.match(r"\s*-\s*intent:\s*\S+", l):
        break
    print(f'{j:4}: {repr(l)}')
    # report if stripped doesn't start with '-'
    stripped = l.lstrip(' \t')
    if stripped and not stripped.startswith('-'):
        print(f'  >> Line {j} does not start with "-" after stripping indent')
