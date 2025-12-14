import json
import sys
from pathlib import Path
p = Path('data/questions.json')
try:
    obj = json.loads(p.read_text(encoding='utf-8'))
except Exception as e:
    print('JSON parse error:', e)
    sys.exit(1)
print('Loaded JSON')
errors = False
for r in ['round_1','round_2']:
    cats = obj.get(r)
    if cats is None:
        print(f'Missing {r}')
        errors = True
        continue
    print(f'{r}: {len(cats)} categories')
    for i,cat in enumerate(cats):
        name = cat.get('category')
        clues = cat.get('clues')
        count = len(clues) if clues else 0
        print(f'  {i+1}: {name} -> {count} clues')
        if not clues or len(clues) != 5:
            print(f'  ERROR: Category "{name}" should have 5 clues (found {count})')
            errors = True
        for j,c in enumerate(clues or []):
            missing = [k for k in ('value','text','answer','type') if k not in c]
            if missing:
                print(f'  ERROR: clue missing fields in {name} clue index {j}: {missing}')
                errors = True
            if 'media' in c:
                m = c['media']
                bad = []
                if 'type' not in m or 'src' not in m:
                    bad.append('type/src')
                if m.get('type') not in ('image','video','audio','iframe','youtube'):
                    bad.append('unsupported-media-type')
                if bad:
                    print(f'  ERROR: media issues in {name} clue index {j}: {bad}')
                    errors = True
if 'final_jeopardy' in obj:
    fj = obj['final_jeopardy']
    if not all(k in fj for k in ('category','text','answer')):
        print('ERROR: final_jeopardy missing fields')
        errors = True
else:
    print('ERROR: final_jeopardy missing')
    errors = True
if errors:
    print('\nValidation completed with errors')
    sys.exit(2)
else:
    print('\nValidation completed - OK')
    sys.exit(0)
