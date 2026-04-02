#!/usr/bin/env python3
"""
Augment intents with templated examples until each intent has at least `--min` examples.

This reuses helper logic from `auto_augment_nlu.py` where possible.
"""
from pathlib import Path
import argparse
import json
import re

# import helpers from auto_augment_nlu if available
from auto_augment_nlu import humanize_intent, add_examples_to_intent, TEMPLATES, NLU_FILE


def collect_existing_examples(nlu_text):
    examples = {}
    current_intent = None
    in_examples = False
    for line in nlu_text.splitlines():
        m = re.match(r'^- intent:\s*(\S+)', line)
        if m:
            current_intent = m.group(1)
            in_examples = False
            continue
        if current_intent and re.match(r'^\s*examples:\s*\|', line):
            in_examples = True
            continue
        if in_examples:
            ex = line.strip()
            if ex.startswith('- '):
                text = ex[2:].strip()
                examples.setdefault(current_intent, []).append(text)
            elif ex == '':
                continue
            else:
                pass
    return examples


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--min', type=int, default=10, help='target minimum examples per intent')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    nlu_path = NLU_FILE
    nlu_text = nlu_path.read_text(encoding='utf-8')
    existing = collect_existing_examples(nlu_text)

    augmented = {}
    for intent, exs in existing.items():
        need = args.min - len(exs)
        if need <= 0:
            continue
        phrase = humanize_intent(intent)
        new_examples = []
        # generate examples from templates, rotate templates if need > templates
        i = 0
        while len(new_examples) < need:
            t = TEMPLATES[i % len(TEMPLATES)]
            ex = t.format(phrase=phrase)
            if ex not in exs and ex not in new_examples:
                new_examples.append(ex)
            i += 1
            # safety: if we cycle too many times, break
            if i > need * 10:
                break

        if new_examples:
            augmented[intent] = new_examples
            if not args.dry_run:
                nlu_text = add_examples_to_intent(nlu_text, intent, new_examples)

    if not args.dry_run:
        nlu_path.write_text(nlu_text, encoding='utf-8')

    print(f'Prepared augmentation for {len(augmented)} intents')
    print(json.dumps(augmented, indent=2))


if __name__ == '__main__':
    main()
