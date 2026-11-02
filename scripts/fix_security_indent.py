#!/usr/bin/env python3
from pathlib import Path
p=Path('bgg-shop-bff/specs/openapi.yaml')
lines=p.read_text().splitlines()
i=0
changed=False
while i < len(lines):
    if lines[i].strip()=="security:":
        # find next responses: or parameters: or requestBody: or tags: to determine indent
        k=i+1
        found=False
        while k < len(lines):
            if lines[k].lstrip().startswith(('responses:','parameters:','requestBody:','tags:','summary:','operationId:','description:')):
                resp_indent=len(lines[k]) - len(lines[k].lstrip())
                found=True
                break
            k+=1
        if not found:
            i+=1
            continue
        # create normalized security block
        sec_line = ' ' * resp_indent + 'security:'
        item_indent = ' ' * (resp_indent + 2)
        items = [item_indent + '- {}', item_indent + '- BearerAuth: []', item_indent + '- XOpKey: []']
        # remove existing block from i to k (exclusive)
        lines = lines[:i] + [sec_line] + items + lines[k:]
        changed=True
        i += 1 + len(items)
    else:
        i += 1
if changed:
    p.write_text('\n'.join(lines)+"\n")
    print('Adjusted security block indentation')
else:
    print('No security blocks found to adjust')
