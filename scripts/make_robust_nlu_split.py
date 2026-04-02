#!/usr/bin/env python3
"""
Create a robust Rasa NLU train/test split.

Rules:
- Collect intents and examples from nlu source files under `data/` and `nlu.yml`.
- For each intent, if total_examples >= `min_total_for_test`, reserve `max(1, int(total*test_frac))`
  examples for test but ensure train retains at least `min_train` examples.
- If an intent has too few examples, keep all in training (no test examples for that intent).

Outputs two files in `train_test_split/`: `training_data.yml` and `test_data.yml`.

Usage:
  python make_robust_nlu_split.py --min-train 8 --test-frac 0.2
"""
from pathlib import Path
import argparse
import re
import random
import os


def collect_examples(paths):
    intent_re = re.compile(r"^\s*-\s*intent:\s*(\S+)")
    examples_re = re.compile(r"^\s*examples:\s*\|")
    intents = {}
    for p in paths:
        text = p.read_text(encoding='utf-8')
        lines = text.splitlines()
        i = 0
        n = len(lines)
        while i < n:
            m = intent_re.match(lines[i])
            if m:
                intent = m.group(1)
                exs = []
                i += 1
                # scan until examples block or next intent
                while i < n and not intent_re.match(lines[i]):
                    if examples_re.match(lines[i]):
                        i += 1
                        while i < n and not intent_re.match(lines[i]) and lines[i].strip() != '':
                            line = lines[i].lstrip()
                            if line.startswith('-'):
                                exs.append(line[1:].strip())
                            i += 1
                        break
                    i += 1
                if exs:
                    intents.setdefault(intent, []).extend(exs)
            else:
                i += 1
    return intents


def write_rasa_nlu(path, intents_map):
    out = []
    out.append('version: "3.1"')
    out.append('nlu:')
    for intent, examples in intents_map.items():
        out.append('\n- intent: %s' % intent)
        out.append('  examples: |')
        for e in examples:
            out.append('    - %s' % e)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(out), encoding='utf-8')


def find_nlu_files(root):
    root = Path(root)
    files = []
    if (root / 'nlu.yml').exists():
        files.append(root / 'nlu.yml')
    data = root / 'data'
    if data.exists():
        for p in data.rglob('*.yml'):
            files.append(p)
    nlu_dir = data / 'nlu'
    if nlu_dir.exists():
        for p in nlu_dir.rglob('*.yml'):
            files.append(p)
    # dedupe
    seen = []
    out = []
    for p in files:
        rp = p.resolve()
        if rp not in seen:
            seen.append(rp)
            out.append(p)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', default='.', help='chatbot folder (default .)')
    p.add_argument('--min-train', type=int, default=8, help='minimum training examples per intent')
    p.add_argument('--min-total-for-test', type=int, default=10, help='minimum total examples for an intent to place any into test')
    p.add_argument('--test-frac', type=float, default=0.2, help='fraction of examples to put into test for eligible intents')
    p.add_argument('--seed', type=int, default=42, help='random seed')
    args = p.parse_args()

    random.seed(args.seed)
    root = Path(args.root)
    files = find_nlu_files(root)
    print('Found %d candidate NLU files' % len(files))
    intents = collect_examples(files)
    print('Collected %d intents' % len(intents))

    train_map = {}
    test_map = {}

    for intent, exs in intents.items():
        total = len(exs)
        if total >= args.min_total_for_test:
            test_count = max(1, int(total * args.test_frac))
            # ensure train remains >= min_train
            if total - test_count < args.min_train:
                test_count = max(0, total - args.min_train)
        else:
            test_count = 0

        exs_copy = list(exs)
        random.shuffle(exs_copy)
        test_examples = exs_copy[:test_count]
        train_examples = exs_copy[test_count:]

        if train_examples:
            train_map[intent] = train_examples
        if test_examples:
            test_map[intent] = test_examples

    out_dir = root / 'train_test_split'
    out_dir.mkdir(exist_ok=True)
    training_file = out_dir / 'training_data.yml'
    test_file = out_dir / 'test_data.yml'

    write_rasa_nlu(training_file, train_map)
    write_rasa_nlu(test_file, test_map)

    print('Wrote %s (%d intents)' % (training_file, len(train_map)))
    print('Wrote %s (%d intents)' % (test_file, len(test_map)))


if __name__ == '__main__':
    main()
