#!/usr/bin/env python3
import os
from pathlib import Path

root = Path('/home/eze/develop/boardgame-app')
changed = []

for p in root.rglob('*.yaml'):
    try:
        s = p.read_text()
    except Exception:
        continue
    if 'BearerAuth' not in s:
        continue
    new = s.replace('        - BearerAuth: []\n', '        - BearerAuth: []\n        - XOpKey: []\n')
    # collapse consecutive duplicates
    while '\n        - XOpKey: []\n        - XOpKey: []\n' in new:
        new = new.replace('\n        - XOpKey: []\n        - XOpKey: []\n', '\n        - XOpKey: []\n')
    if new != s:
        p.write_text(new)
        changed.append(str(p))

if changed:
    print('Modified files:')
    for c in changed:
        print(c)
else:
    print('No files changed')
