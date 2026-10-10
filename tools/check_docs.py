"""Check public Markdown's local links and image paths; no network/model calls."""
from __future__ import annotations
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

def public_markdown():
    paths = set()
    for args in [('ls-files','-z','--','*.md'),('ls-files','--others','--exclude-standard','-z','--','*.md')]:
        result = subprocess.run(['git',*args],cwd=ROOT,check=True,capture_output=True)
        paths.update(p for p in result.stdout.decode('utf-8').split('\0') if p)
    return sorted(p for p in paths if (ROOT/p).is_file() and p != 'docs/resume-draft.md')

def check():
    errors, links = [], 0
    documents = public_markdown()
    for relative in documents:
        path = ROOT/relative
        body = path.read_text(encoding='utf-8')
        prose = re.sub(r'^```[^\n]*\n.*?^```\s*$', '', body, flags=re.M|re.S)
        for match in re.finditer(r'!?\[[^\]\n]*\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)',prose):
            raw = match.group(1).strip('<>')
            target = urlsplit(raw)
            if target.scheme or target.netloc:
                continue
            links += 1
            destination = (path.parent/unquote(target.path)).resolve() if target.path else path
            if not destination.exists():
                errors.append(f'{relative}: missing target {raw}')
            elif target.fragment and destination.suffix == '.md' and target.fragment.isascii():
                headings = re.findall(r'^#{1,6}\s+(.+?)\s*#*$', destination.read_text(encoding='utf-8'),re.M)
                slugs = {re.sub(r'[^\w\- ]','',h.lower()).replace(' ','-') for h in headings}
                if unquote(target.fragment) not in slugs:
                    errors.append(f'{relative}: missing heading {raw}')
    for error in errors:
        print(error)
    print(f'Checked {len(documents)} public Markdown files and {links} local links/images; {len(errors)} errors.')
    print('External URLs, binary image content, and live service availability are not checked.')
    return 1 if errors else 0

if __name__ == '__main__':
    raise SystemExit(check())
