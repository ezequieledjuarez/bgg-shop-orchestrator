#!/usr/bin/env python3
import re
from pathlib import Path
p=Path('bgg-shop-bff/specs/openapi.yaml')
s=p.read_text()
# 1) Collapse multiple XOpKey lines following a BearerAuth into a single one, preserving indent
pattern=re.compile(r"(\n([ \t]*)- BearerAuth: \[\]\n)(?:[ \t]*- XOpKey: \[\]\n)+", re.M)
s_new=pattern.sub(lambda m: f"\n{m.group(2)}- BearerAuth: []\n{m.group(2)}- XOpKey: []\n", s)
# 2) Where BearerAuth exists but no XOpKey after, insert one
pattern2=re.compile(r"(\n([ \t]*)- BearerAuth: \[\]\n)(?![ \t]*- XOpKey: \[\])", re.M)
s_new=pattern2.sub(lambda m: f"\n{m.group(2)}- BearerAuth: []\n{m.group(2)}- XOpKey: []\n", s_new)
# 3) Remove stray standalone duplicate XOpKey lines (more than one consecutively)
s_new=re.sub(r"(\n[ \t]*- XOpKey: \[\]\n){2,}","\n        - XOpKey: []\n", s_new)
# 4) Remove accidental 'security:' followed by misplaced lines: ensure 'security:' line has correct following items
# We'll normalize any 'security:' section to align items under it
s_new=re.sub(r"\nsecurity:\n([ \t\S\n]{0,200}?)(\n\s*responses:|\n\s*parameters:|\n\s*/|\n\s*$)", lambda m: '\nsecurity:\n        - {}\n        - BearerAuth: []\n        - XOpKey: []\n'+m.group(2), s_new, flags=re.M)

if s_new!=s:
    p.write_text(s_new)
    print('Updated openapi.yaml')
else:
    print('No changes applied')
