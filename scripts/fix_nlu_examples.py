import re
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'nlu.yml'
backup = p.with_suffix('.yml.bak')
text = p.read_text(encoding='utf-8')
backup.write_text(text, encoding='utf-8')

lines = text.splitlines()
out_lines = []
i = 0
n = len(lines)
while i < n:
    line = lines[i]
    out_lines.append(line)
    # detect an examples block
    if re.match(r"\s*examples:\s*\|\s*$", line):
        i += 1
        # consume following indented block lines
        # determine indent level from first following line
        block_lines = []
        while i < n and (lines[i].strip() == '' or lines[i].startswith(' ') or lines[i].startswith('\t')):
            block_lines.append(lines[i])
            i += 1
        # process block_lines: ensure each non-empty example line starts with '- '
        fixed_block = []
        for bl in block_lines:
            stripped = bl.lstrip('\t ')
            if stripped == '':
                fixed_block.append(bl)
                continue
            if not stripped.startswith('-'):
                # determine current indentation
                indent = bl[:len(bl)-len(stripped)]
                fixed_block.append(f"{indent}- {stripped}")
            else:
                # normalize single dash spacing
                indent = bl[:len(bl)-len(stripped)]
                after = stripped
                if not after.startswith('- '):
                    after = after.replace('-', '-', 1)
                    if after.startswith('-') and len(after) > 1 and after[1] != ' ':
                        after = '- ' + after[1:].lstrip()
                fixed_block.append(f"{indent}{after}")
        out_lines.extend(fixed_block)
        continue
    i += 1

new_text = '\n'.join(out_lines) + ('\n' if text.endswith('\n') else '')
if new_text != text:
    p.write_text(new_text, encoding='utf-8')
    print(f'Fixed formatting in {p} (backup at {backup})')
else:
    print('No formatting changes needed.')
