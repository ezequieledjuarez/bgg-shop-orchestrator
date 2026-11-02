#!/usr/bin/env python3
from pathlib import Path
p=Path('bgg-shop-bff/specs/openapi.yaml')
lines=p.read_text().splitlines()
indents=[len(l)-len(l.lstrip(' ')) for l in lines if l.strip()!='' and l.startswith(' ')]
if indents:
    min_indent=min(indents)
else:
    min_indent=0
if min_indent>0:
    new='\n'.join([l[min_indent:] if l.startswith(' '*min_indent) else l for l in lines])
    p.write_text(new)
    print(f'Removed common indent of {min_indent} spaces')
else:
    print('No common indent to remove')
