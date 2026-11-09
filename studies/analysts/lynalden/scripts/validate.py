"""Validate the public audit's records, rendered coverage and internal links."""
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
EXPECTED = {'right': 1402, 'wrong': 327, 'mixed': 2011, 'not_testable': 1405,
            'too_early': 286, 'conditional_pending': 139, 'evidence_needed': 715}
errors = []


def check(condition, message):
    if not condition:
        errors.append(message)


class Page(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.ids, self.links = set(), []
        self.feed(content)
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values:
            check(values['id'] not in self.ids, 'Duplicate HTML ID: ' + values['id'])
            self.ids.add(values['id'])
        for key in ['href', 'src']:
            if values.get(key):
                self.links.append(values[key])


metadata = {x['id']: x for x in json.loads((DATA / 'article-metadata.json').read_text())}
reviews = [json.loads(p.read_text()) for p in sorted((DATA / 'reviews').glob('[0-9][0-9][0-9].json'))]
counts = Counter()
ids = set()
check(len(reviews) == len(metadata) == 200, 'Expected 200 article reviews and source records')
check(len(list((ROOT / 'articles').glob('[0-9][0-9][0-9].md'))) == 200, 'Expected 200 Markdown article reviews')
check(len(list((ROOT / 'report').glob('article-*.html'))) == 200, 'Expected 200 HTML article reviews')
pages = {p: Page(p.read_text()) for p in (ROOT / 'report').glob('*.html')}

for r in reviews:
    aid = r['article_id']
    source = metadata[aid]
    check(r['read_complete'], aid + ': incomplete reading')
    check(r['source_url'] == source['url'], aid + ': source URL mismatch')
    check(r['date'] == source['publication_date'], aid + ': date mismatch')
    check(bool(re.fullmatch(r'[0-9a-f]{64}', source['source_sha256'])), aid + ': invalid source hash')
    if r.get('source_sha256'):
        check(r['source_sha256'] == source['source_sha256'], aid + ': source hash mismatch')
    page = pages[ROOT / 'report' / f'article-{aid}.html']
    markdown = (ROOT / 'articles' / f'{aid}.md').read_text()
    for c in r['claims']:
        cid = c['id']
        check(cid not in ids, cid + ': duplicate claim ID')
        ids.add(cid)
        counts[c['verdict']] += 1
        check(cid in page.ids, cid + ': missing HTML claim anchor')
        check(f'### {cid}\n' in markdown, cid + ': missing Markdown claim heading')
        check(bool(c.get('reason')), cid + ': missing assessment')
        check(bool(c.get('source_blocks')) and set(c['source_blocks']) <= set(source['source_block_ids']), cid + ': invalid source blocks')
        evidence = [e for e in c.get('evidence', []) if e.get('verified') and e.get('finding') and e.get('url', '').startswith('https://')]
        proof = c.get('proof') or {}
        deductive = c.get('kind') == 'explanation' and c.get('evidence_basis') == 'deductive' and proof.get('assumptions') and proof.get('derivation')
        if c['verdict'] in {'right', 'wrong'}:
            check(bool(evidence or deductive), cid + ': resolved claim lacks evidence or bounded proof')
        if c['verdict'] == 'too_early':
            check(bool(c.get('horizon') or c.get('next_check')), cid + ': future test not specified')
        for e in c.get('evidence', []):
            if e.get('date'):
                check(date.fromisoformat(e['date']) <= date(2026, 11, 7), cid + ': post-cutoff evidence')
check(dict(counts) == EXPECTED, 'Verdict counts changed')

audit = json.loads((ROOT / 'report/audit-data.json').read_text())
check(len(audit['articles']) == 200 and len(audit['claims']) == 6285, 'Searchable data coverage mismatch')
check({c['id'] for c in audit['claims']} == ids, 'Searchable data claim IDs differ from canonical records')
embedded = re.search(r'<script id="audit-data" type="application/json">(.*?)</script>', (ROOT / 'report/index.html').read_text(), re.S)
check(bool(embedded) and json.loads(embedded.group(1)) == audit, 'Embedded search data differs from downloaded scorecard')

link_count = 0
def validate_link(path, link):
    global link_count
    parsed = urlsplit(link.strip('<>'))
    if parsed.scheme or parsed.netloc:
        return
    if not parsed.path and not parsed.fragment:
        return
    target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path.resolve()
    link_count += 1
    check(target.is_relative_to(ROOT.resolve()), f'{path.name}: link escapes study: {link}')
    check(target.exists(), f'{path.name}: missing linked file: {link}')
    if parsed.fragment and target.exists():
        fragment = unquote(parsed.fragment)
        if target.suffix == '.html':
            check(fragment in pages[target].ids, f'{path.name}: missing HTML anchor: {link}')
        elif target.suffix == '.md':
            headings = re.findall(r'^#{1,6} (.+)$', target.read_text(), re.M)
            slugs = {re.sub(r'[^\w\- ]', '', h.lower()).replace(' ', '-') for h in headings}
            check(fragment in slugs, f'{path.name}: missing Markdown anchor: {link}')

for path, page in pages.items():
    for link in page.links:
        validate_link(path, link)
for path in ROOT.rglob('*.md'):
    for link in re.findall(r'\]\(([^\s)]+)\)', path.read_text()):
        validate_link(path, link)

for path in ROOT.rglob('*'):
    if not path.is_file() or '__pycache__' in path.parts:
        continue
    if path.suffix in {'.json', '.md', '.html'}:
        text = path.read_text()
        check('/Users/' not in text and '/private/tmp/' not in text, f'{path.name}: private local path')
        check('\u2014' not in text, f'{path.name}: em dash')
        check(not re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+', text), f'{path.name}: possible credential')
    check(path.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.xlsx', '.zip'}, f'{path.name}: unexpected source asset')
check(not (ROOT / 'sources').exists() and not (DATA / 'sources').exists(), 'Private source corpus must not be published')

result = {'as_of': '2026-11-07', 'article_reviews': len(reviews), 'claim_occurrences': sum(counts.values()),
          'verdicts': dict(counts), 'local_links_checked': link_count, 'errors': errors}
print(json.dumps(result, indent=2))
raise SystemExit(bool(errors))
