# SPDX-License-Identifier: GPL-3.0-only
"""Pre-publication guard: inspect the exact staged tree, never the private workspace."""
from pathlib import Path
import re,subprocess,sys
root=Path(__file__).resolve().parents[1]
names=subprocess.check_output(['git','diff','--cached','--name-only','--diff-filter=ACMR','-z'],cwd=root).decode().split('\0')
errors=[]
for name in filter(None,names):
    p=root/name
    if any(part in ('build','.gradle','private-signing') for part in p.relative_to(root).parts):errors.append(name+': generated/private directory')
    if p.suffix.lower() in ('.jks','.p12','.keystore','.key','.apk','.wasm','.data','.fcstd','.log'):errors.append(name+': forbidden publication file')
    if p.stat().st_size>5_000_000:errors.append(name+': unexpected large source file')
    try:text=p.read_text(encoding='utf-8')
    except UnicodeDecodeError:continue
    for pattern in (r'[A-Z]:[\\/]Users[\\/]',r'[A-Z]:[\\/]03_Projekty[\\/]',r'github_pat_[A-Za-z0-9_]+',r'gh[pousr]_[A-Za-z0-9]{25,}',r'-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----'):
        if re.search(pattern,text,re.I):errors.append(name+': private material pattern')
if errors:raise SystemExit('\n'.join(errors))
print('Staged source privacy/size guard passed:',len(list(filter(None,names))),'files')
