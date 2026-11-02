#!/usr/bin/env python3
from pathlib import Path
p=Path('bgg-shop-bff/specs/openapi.yaml')
text=p.read_text()
lines=text.splitlines()
top_keys=('openapi:','info:','paths:','components:','servers:','security:')
new_lines=[]
for l in lines:
    stripped=l.lstrip(' ')
    if any(stripped.startswith(k) for k in top_keys):
        new_lines.append(stripped)
    else:
        new_lines.append(l)
new='\n'.join(new_lines)
p.write_text(new)
print('Normalized top-level keys')
