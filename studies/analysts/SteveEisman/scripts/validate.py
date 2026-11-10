"""Validate coverage, evidence schema, provenance and generated navigation.

Default mode permits explicitly pending reviews during research. Release mode
requires every inventory item and the archive synthesis to be complete.
"""
import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlsplit, unquote

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--require-complete',action='store_true')
parser.add_argument('--private-root',type=Path,help='Optionally verify hashes against captured local sources')
args=parser.parse_args()
raw_hashes=set()
if args.private_root:
    raw_hashes={hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (args.private_root/'transcripts').iterdir() if p.is_file()}
errors=[]
def check(condition,message):
    if not condition:errors.append(message)
def read(path):return json.loads(path.read_text())
catalog=read(ROOT/'data/catalog.json')
reviews={p.stem:read(p) for p in (ROOT/'data/reviews').glob('*.json')}
unitmap={u['id']:u for u in catalog['units']}
check(len(unitmap)==len(catalog['units']),'Duplicate review-unit ID')
check(len(catalog['listings'])==358,'Inventory listing count changed; reconcile scope')
check(len(unitmap)==192,'Review-unit count changed; reconcile aliases')
listing_ids=[(x['platform'],x['listing_id']) for x in catalog['listings']]
check(len(set(listing_ids))==len(listing_ids),'Duplicate platform listing')
check(dict(Counter(x['platform'] for x in catalog['listings']))==catalog['listing_counts'],'Platform counts disagree')
for row in catalog['listings']:
    check(row['review_unit_id'] in unitmap,'Listing points to missing review')

verdicts={'right','wrong','mixed','too_early','unresolved','not_testable'}
kinds={'forecast','explanation','investment thesis','analytical principle','material factual premise',
       'investment preference','investment valuation','investment framework','conditional scenario',
       'political assessment','normative judgment'}
claims={}
claim_units={}
for uid,u in unitmap.items():
    sid=u['review_source_id']
    check(u['source_captured'],f'{uid}: source not captured')
    r=reviews.get(sid)
    if not r:
        check(not args.require_complete,f'{uid}: review missing')
        continue
    check(r['source_id']==sid,f'{uid}: source ID mismatch')
    check(r.get('read_complete') is True,f'{uid}: incomplete source read')
    check(r['evaluation_as_of']==catalog['audit_cutoff'],f'{uid}: cutoff mismatch')
    check(r['transcript_sha256']==u['transcript']['transcript_sha256'],f'{uid}: catalog/source hash mismatch')
    check(bool(re.fullmatch('[0-9a-f]{64}',r['transcript_sha256'])),f'{uid}: invalid source hash')
    if args.private_root:
        n=read(args.private_root/'normalized'/f'{sid}.json')
        check(n['metadata']['transcript_sha256']==r['transcript_sha256'],f'{uid}: local source hash mismatch')
        check(r['transcript_sha256'] in raw_hashes,f'{uid}: no matching captured source artifact')
    check(bool(r.get('summary')) and bool(r.get('assessment')),f'{uid}: missing summary or assessment')
    check(bool(r['claims']) or bool(r.get('excerpt_of')),f'{uid}: no claims or excerpt attribution')
    if r.get('excerpt_of'):check(r['excerpt_of'] in unitmap,f'{uid}: missing excerpt parent')
    for c in r['claims']:
        cid=c['id']
        check(cid not in claims,f'Duplicate claim ID: {cid}')
        claims[cid]=c;claim_units[cid]=uid
        for key in ['claim','speaker','stance','kind','horizon','test','verdict','reason','next_check','family','materiality','synthesis_role']:
            check(bool(c.get(key)),f'{cid}: missing {key}')
        check(c['verdict'] in verdicts,f'{cid}: invalid verdict')
        check(c['kind'] in kinds,f'{cid}: invalid kind')
        check(c['materiality'] in {'major','supporting'},f'{cid}: invalid materiality')
        start,end=c.get('start_seconds'),c.get('end_seconds')
        if u['format']!='article':
            check(isinstance(start,(int,float)) and isinstance(end,(int,float)),f'{cid}: invalid timestamps')
            if isinstance(start,(int,float)) and isinstance(end,(int,float)):
                check(0<=start<=end,f'{cid}: inverted timestamps')
                duration=u.get('duration_seconds')
                check(not duration or end<=duration+15,f'{cid}: citation beyond media duration')
        proof=c.get('proof')
        if proof:check(bool(proof.get('derivation')) if isinstance(proof,dict) else bool(proof),f'{cid}: empty proof')
        if c['verdict'] in {'right','wrong','mixed'}:
            check(bool(c.get('evidence')) or bool(proof),f'{cid}: resolved without evidence or derivation')
        for e in c.get('evidence',[]):
            check(bool(e.get('finding')),f'{cid}: evidence has no finding')
            check(e.get('verified') is True,f'{cid}: attached evidence was not inspected')
            check(urlsplit(e['url']).scheme=='https',f'{cid}: evidence requires HTTPS')

def inspect(value,path='data'):
    if isinstance(value,dict):
        for k,v in value.items():
            check(k not in {'segments','raw_text','body_html','body_json','audio_url','signed_url','cookies'},f'{path}: private source field {k}')
            inspect(v,path+'.'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value):inspect(v,f'{path}[{i}]')
    elif isinstance(value,str):
        check('\u2014' not in value,f'{path}: em dash')
        for url in re.findall(r'https?://[^\s<>"\]]+',value):
            keys={k.lower() for k,v in parse_qsl(urlsplit(url).query)}
            check(not keys.intersection({'token','access_token','signature','x-amz-signature','x-amz-credential','x-amz-security-token','authorization'}),f'{path}: signed access URL')
inspect(catalog)
for sid,r in reviews.items():inspect(r,sid)

synthfile=ROOT/'data/synthesis.json'
check(synthfile.exists() or not args.require_complete,'Archive synthesis missing')
if synthfile.exists():
    synthesis=read(synthfile);inspect(synthesis,'synthesis')
    for key in ['summary','takes','repeated','framework','tools']:
        check(bool(synthesis.get(key)),f'Synthesis missing {key}')
        for section in synthesis.get(key,{}).get('sections',[]):
            for cid in section.get('claim_ids',[]):check(cid in claims,f'Synthesis reference missing: {cid}')

class Links(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and 'href' in a:self.links.append(a['href'])

for path in (ROOT/'report').glob('*.html'):
    page=Links();page.feed(path.read_text())
    check(len(page.ids)==len(set(page.ids)),f'{path.name}: duplicate HTML ID')
    for href in page.links:
        if href.startswith('#episode/'):
            bits=unquote(href).split('/')
            check(bits[1] in unitmap,f'{path.name}: missing episode route')
            if len(bits)>2:check(bits[2] in claims and claim_units.get(bits[2])==bits[1],f'{path.name}: missing claim route')
        elif not urlsplit(href).scheme and not href.startswith('#'):
            check((path.parent/unquote(href.split('#')[0])).exists(),f'{path.name}: broken local link {href}')
for uid in unitmap:
    check((ROOT/'report'/f'{uid}.html').exists(),f'{uid}: HTML page missing')
    check((ROOT/'episodes'/f'{uid}.md').exists(),f'{uid}: Markdown page missing')
if errors:
    print('\n'.join(errors))
    raise SystemExit(f'{len(errors)} validation errors')
print(f'Validated {len(unitmap)} review units, {len(reviews)} reviews, {len(claims):,} claims and 358 source listings.')
