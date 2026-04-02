import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
INTENT_REPORT = BASE / 'results' / 'intent_report.json'
NLU_FILE = BASE / 'nlu.yml'
DUP_REPORT = BASE / 'results' / 'duplicate_examples_report.md'
AUGMENTED_LIST = BASE / 'results' / 'augmented_intents.json'

TEMPLATES = [
    "How do I {phrase}?",
    "What is the {phrase}?",
    "Where can I find information about {phrase}?",
]


def humanize_intent(intent_name):
    # remove common prefixes
    phrase = re.sub(r'^(ask_|get_|update_|select_|choose_|raise_|track_|close_|report_)', '', intent_name)
    phrase = phrase.replace('_', ' ')
    # simple tweaks
    phrase = phrase.replace('cbit', 'CBIT')
    return phrase


def load_intent_report():
    return json.loads(INTENT_REPORT.read_text(encoding='utf-8'))


def collect_existing_examples(nlu_text):
    # find all examples under intents
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
                examples.setdefault(text, set()).add(current_intent)
            elif ex == '':
                continue
            else:
                # end of examples block if next intent or section begins
                pass
    return examples


def add_examples_to_intent(nlu_text, intent, new_examples):
    pattern = re.compile(r'(^- intent:\s*' + re.escape(intent) + r"\b.*?)(?=\n- intent: |\Z)", re.S | re.M)
    m = pattern.search(nlu_text)
    block = '\n'.join([f"- intent: {intent}", "  examples: |"] + [f"    - {e}" for e in new_examples])
    if m:
        # found existing block, insert examples at end of examples section
        start, end = m.span()
        block_text = m.group(1)
        # find examples: | inside block
        ex_m = re.search(r'(examples:\s*\|)', block_text)
        if ex_m:
            # append at end of block before next intent
            insertion = '\n' + '\n'.join([f"    - {e}" for e in new_examples])
            # find position to insert: before the next '- intent:' or end
            nlu_text = nlu_text[:end]  # take full matched as we'll replace
            # replace matched with itself plus insertion
            new_block = m.group(0) + insertion
            nlu_text = nlu_text[:start] + new_block + nlu_text[end:]
            return nlu_text
        else:
            # no examples found, replace whole intent block with new block
            nlu_text = nlu_text[:start] + block + nlu_text[end:]
            return nlu_text
    else:
        # intent not present, append at end
        if not nlu_text.endswith('\n'):
            nlu_text += '\n'
        nlu_text += '\n' + block + '\n'
        return nlu_text


def main():
    intent_report = load_intent_report()
    nlu_text = NLU_FILE.read_text(encoding='utf-8')
    existing_examples = collect_existing_examples(nlu_text)

    intents_to_augment = []
    for intent, stats in intent_report.items():
        try:
            f1 = float(stats.get('f1-score', 0.0))
            support = int(stats.get('support', 0))
        except Exception:
            continue
        if f1 == 0.0 and support >= 5:
            intents_to_augment.append(intent)

    augmented = {}
    for intent in intents_to_augment:
        phrase = humanize_intent(intent)
        new_examples = []
        for t in TEMPLATES:
            ex = t.format(phrase=phrase)
            # avoid duplicates
            if ex in existing_examples:
                # if already exists but associated with different intent, still add to augmented list for review
                existing_examples.setdefault(ex, set()).add(intent)
            else:
                new_examples.append(ex)
                existing_examples.setdefault(ex, set()).add(intent)
        if new_examples:
            nlu_text = add_examples_to_intent(nlu_text, intent, new_examples)
            augmented[intent] = new_examples

    # write back nlu.yml
    NLU_FILE.write_text(nlu_text, encoding='utf-8')

    # write augmented list
    AUGMENTED_LIST.write_text(json.dumps(augmented, indent=2), encoding='utf-8')

    # duplicate examples report
    duplicates = {text: list(intents) for text, intents in existing_examples.items() if len(intents) > 1}
    report_lines = ["# Duplicate example texts (same text labeled with multiple intents)", ""]
    if duplicates:
        for text, intents in duplicates.items():
            report_lines.append(f"- '{text}': {', '.join(intents)}")
    else:
        report_lines.append('No duplicate examples found.')
    DUP_REPORT.write_text('\n'.join(report_lines), encoding='utf-8')

    print(f"Augmented {len(augmented)} intents. Duplicates: {len(duplicates)}")


if __name__ == '__main__':
    main()
