import os
import yaml

EXTS = ('.yml', '.yaml', '.json')

def scan(root='.'):
    issues = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.lower().endswith(EXTS):
                path = os.path.join(dirpath, fn)
                try:
                    with open(path, 'r', encoding='utf-8') as fh:
                        txt = fh.read()
                    data = yaml.safe_load(txt)
                    if not isinstance(data, (dict, list)):
                        issues.append((path, type(data).__name__, txt[:400].replace('\n', ' ')))
                except Exception as e:
                    issues.append((path, 'PARSE_ERROR', str(e)))
    return issues

if __name__ == '__main__':
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    issues = scan(root)
    if not issues:
        print('OK: no malformed top-level NLU files found')
    else:
        for p, kind, info in issues:
            print(f'{kind}: {p}')
            print(info)
            print('---')
