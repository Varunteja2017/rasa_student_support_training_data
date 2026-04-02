from pathlib import Path
import re
from collections import defaultdict

p = Path(__file__).resolve().parents[1] / 'nlu.yml'
text = p.read_text(encoding='utf-8')

intent = None
examples_block = False
examples = []
intent_examples = defaultdict(list)
for line in text.splitlines():
    m = re.match(r"\s*-\s*intent:\s*(\S+)", line)
    if m:
        intent = m.group(1)
        examples_block = False
        continue
    if intent and re.match(r"\s*examples:\s*\|", line):
        examples_block = True
        continue
    if examples_block:
        if line.strip() == '':
            continue
        # if next intent starts, break
        if re.match(r"\s*-\s*intent:\s*(\S+)", line):
            examples_block = False
            intent = None
            continue
        stripped = line.lstrip(' \t')
        if stripped.startswith('-'):
            ex = stripped[1:].strip()
            if ex:
                intent_examples[ex].append(intent)

# write report
res_dir = Path(__file__).resolve().parents[1] / 'results'
res_dir.mkdir(exist_ok=True)
rep = res_dir / 'duplicate_examples_report.md'
lines = ["# Duplicate training examples report\n"]
dups = {k: v for k, v in intent_examples.items() if len(set(v)) > 1}
if not dups:
    lines.append('\nNo duplicates found.\n')
else:
    for ex, intents in sorted(dups.items(), key=lambda x: (-len(set(x[1])), x[0])):
        lines.append(f"- **Example:** {ex}\n  - Intents: {', '.join(sorted(set(intents)))}\n")
rep.write_text('\n'.join(lines), encoding='utf-8')
print(f'Wrote duplicate report to {rep}')
