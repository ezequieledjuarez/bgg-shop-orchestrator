#!/usr/bin/env python3
from pathlib import Path
p=Path('bgg-shop-bff/specs/openapi.yaml')
s=p.read_text()
occ=[i for i in range(len(s)) if s.startswith('openapi:', i)]
if len(occ)>=2:
    start=occ[1]
    new=s[start:]
    p.write_text(new)
    print('Rewrote file starting from second openapi occurrence')
else:
    print('No duplicate openapi header found; no action')
