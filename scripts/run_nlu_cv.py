#!/usr/bin/env python3
"""
Run repeated-split evaluation for Rasa NLU locally.

This script automates:
 - generating a robust split (`make_robust_nlu_split.py`)
 - training NLU on the training file
 - testing on the test file
 - collecting per-run metrics from `results/nlu_report.json` (if produced)

Usage (from `chatbot/`):
  venv\Scripts\python.exe scripts\run_nlu_cv.py --runs 5 --min-train 8 --test-frac 0.2

Note: training is compute-intensive; run this locally where `rasa` is installed in the virtualenv.
"""
from pathlib import Path
import argparse
import subprocess
import json
import os
import statistics


def run_cmd(cmd, cwd='.', timeout=None):
    print('>',' '.join(cmd))
    rc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return rc


def collect_metrics(results_dir):
    # look for nlu_report.json
    p = Path(results_dir) / 'nlu_report.json'
    if not p.exists():
        # try results/nlu.json or results/nlu_report.json in cwd
        return None
    obj = json.loads(p.read_text(encoding='utf-8'))
    # example Rasa JSON contains per-intent metrics and overall accuracy; try to extract
    overall = obj.get('overall') or obj.get('accuracy') or {}
    return obj


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runs', type=int, default=5)
    p.add_argument('--min-train', type=int, default=8)
    p.add_argument('--test-frac', type=float, default=0.2)
    p.add_argument('--venv-python', default=os.path.join('venv','Scripts','python.exe'))
    p.add_argument('--timeout-train', type=int, default=1800)
    args = p.parse_args()

    py = args.venv_python
    cwd = Path('.')
    models = []
    aggregated = []

    for run in range(1, args.runs+1):
        print(f'=== Run {run}/{args.runs} ===')
        seed = 1000 + run
        # generate split with seed by setting environment or reusing script (seed not currently parameterized)
        rc = run_cmd([py, 'scripts/make_robust_nlu_split.py', '--min-train', str(args.min_train), '--test-frac', str(args.test_frac)])
        if rc.returncode != 0:
            print('split failed', rc.stderr)
            continue

        # train
        train_cmd = [py, '-m', 'rasa', 'train', 'nlu', '--nlu', 'train_test_split/training_data.yml', '--config', 'config.yml', '--out', 'models']
        rc2 = run_cmd(train_cmd, timeout=args.timeout_train)
        if rc2.returncode != 0:
            print('train failed', rc2.stderr)
            continue

        # pick latest model
        models_dir = Path('models')
        cand = sorted([p for p in models_dir.iterdir() if p.suffix == '.gz' or p.name.endswith('.tar.gz')], key=lambda x: x.stat().st_mtime)
        if not cand:
            print('no model produced')
            continue
        model = str(cand[-1])

        # test
        test_cmd = [py, '-m', 'rasa', 'test', 'nlu', '--nlu', 'train_test_split/test_data.yml', '--model', model, '--out', 'results']
        rc3 = run_cmd(test_cmd, timeout=600)
        if rc3.returncode != 0:
            print('test failed', rc3.stderr)
            continue

        # collect metrics
        metrics = collect_metrics('results')
        aggregated.append(metrics)
        print('run metrics collected')

    # Summarize
    successful = [m for m in aggregated if m]
    print('\nSummary:')
    print(f'Runs: attempted={args.runs} successful={len(successful)}')
    # dump aggregated json
    Path('results').mkdir(exist_ok=True)
    Path('results/nlu_cv_aggregated.json').write_text(json.dumps(aggregated, indent=2), encoding='utf-8')
    print('Wrote results/nlu_cv_aggregated.json')


if __name__ == '__main__':
    main()
