"""Build offline HTML and Markdown from original analysis and public provenance."""
from collections import Counter
from pathlib import Path
import html
import json
import re

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'
OUT=ROOT/'report'
MD=ROOT/'episodes'
OUT.mkdir(exist_ok=True)
MD.mkdir(exist_ok=True)
catalog=json.loads((DATA/'catalog.json').read_text())
method=json.loads((DATA/'methodology.json').read_text())
synthesis=json.loads((DATA/'synthesis.json').read_text()) if (DATA/'synthesis.json').exists() else {}
reviews={p.stem:json.loads(p.read_text()) for p in (DATA/'reviews').glob('*.json')}
labels={'right':'Right','wrong':'Wrong','mixed':'Mixed','too_early':'Too early','unresolved':'Unresolved','not_testable':'Not testable'}
E=lambda s:html.escape(str(s or ''))

def ts(seconds):
    n=int(seconds or 0)
    return f'{n//3600}:{n%3600//60:02}:{n%60:02}' if n>=3600 else f'{n//60}:{n%60:02}'

def location(c,u):
    paragraphs=c.get('paragraph_references') or c.get('paragraphs') or c.get('source_paragraphs') or c.get('paragraph')
    if u['format']=='article':
        return c.get('source_locator') or (('Paragraphs '+', '.join(map(str,paragraphs))) if isinstance(paragraphs,list) else ('Paragraph '+str(paragraphs)) if paragraphs else 'Article passage')
    return ts(c.get('start_seconds'))+'-'+ts(c.get('end_seconds'))

def source_href(c,u):
    url=u['reviewed_version_url']
    if 'youtube.com/watch?' in url and c.get('start_seconds') is not None:
        return url+'&t='+str(int(c['start_seconds']))+'s'
    return url

def badge(v,n=None):
    return '<span class="badge '+E(v)+'">'+E(labels.get(v,v))+(' · '+str(n) if n is not None else '')+'</span>'

def ul(values):
    return '<ul>'+''.join('<li>'+E(v)+'</li>' for v in values)+'</ul>' if values else ''

def prose(value):
    return ''.join('<p>'+E(x)+'</p>' for x in (value if isinstance(value,list) else [value])) if value else ''

def followup(c):
    value=c.get('next_check') or ''
    if value==c.get('test'):return ''
    if c['verdict'] in {'right','wrong','mixed'} and value=='Obtain primary evidence matching the stated metric, period and conditions before assigning an outcome grade.':return ''
    return value

def claim_html(c,u):
    facts=[('Speaker',c['speaker']),('Stance',c.get('stance')),('Horizon',c.get('horizon')),('Materiality',c.get('materiality','not classified'))]
    ev=''.join('<li><a target="_blank" rel="noopener" href="'+E(x['url'])+'">'+E(x.get('title') or x.get('publisher') or x['url'])+'</a>'+(' · '+E(x['date']) if x.get('date') else '')+(' <b>[not independently inspected]</b>' if not x.get('verified') else '')+'<br>'+E(x.get('finding'))+'</li>' for x in c.get('evidence',[]))
    proof=c.get('proof')
    deductive=''
    if proof:
        deductive='<div class="note"><b>Conditional reasoning</b>'+prose(proof.get('derivation') if isinstance(proof,dict) else proof)+(ul(proof.get('assumptions',[])) if isinstance(proof,dict) and isinstance(proof.get('assumptions'),list) else '')+'</div>'
    return '<section class="claim-card" id="'+E(c['id'])+'"><div class="claim-top"><div><div class="meta">'+E(c['id'])+' · '+E(c.get('kind'))+'</div><h3>'+E(c['claim'])+'</h3></div>'+badge(c['verdict'])+'</div><a class="source-stamp" target="_blank" rel="noopener" href="'+E(source_href(c,u))+'">Source · '+E(location(c,u))+' ↗</a><div class="spec">'+''.join('<div><b>'+E(k)+'</b>'+E(v or 'Not stated')+'</div>' for k,v in facts)+'</div>'+prose(c['reason'])+(prose('Qualification: '+c['qualifications']) if c.get('qualifications') else '')+deductive+'<p class="small"><b>Assessment test:</b> '+E(c.get('test'))+'</p>'+('<p class="small"><b>Further verification:</b> '+E(followup(c))+'</p>' if followup(c) else '')+'<details><summary>Evidence and assessment details</summary><p class="small">Attribution confidence: '+E(c.get('attribution_confidence'))+'. Assessment confidence: '+E(c.get('confidence'))+'. Thesis family: '+E(c.get('family'))+'.</p>'+('<ul class="evidence">'+ev+'</ul>' if ev else '<p class="muted">No independent empirical outcome evidence is attached. A principle, disclosure or unfinished forecast is not a verified investment win.</p>')+'</details></section>'

units=[]
allclaims=[]
for u in catalog['units']:
    r=reviews.get(u['review_source_id'])
    item={**u,'review':r}
    item['counts']=dict(Counter(c['verdict'] for c in r['claims'])) if r else {}
    item['claim_count']=len(r['claims']) if r else 0
    units.append(item)
    if r:
        for c in r['claims']:
            allclaims.append({**c,'unit_id':u['id'],'unit_title':u['title'],'date':u['first_listed_publication'][:10],
                              'source_href':source_href(c,u),'source_location':location(c,u)})

def episode_body(u):
    r=u['review']
    dates='<div class="meta">First listed '+E(u['first_listed_publication'][:10])+' · '+E(u['format'].replace('_',' '))+'</div>'
    body='<div class="article-header">'+dates+'<h1>'+E(u['title'])+'</h1>'+prose(r['summary'] if r else 'This item is inventoried. Its review is not yet complete.')+'</div>'
    body+='<div class="source-list">'+''.join('<a target="_blank" rel="noopener" href="'+E(x['url'])+'">'+E(x['platform'])+' · '+E(x['published_at'][:10])+' ↗</a>' for x in u['listings'])+'</div>'
    if not r:return body+'<div class="note">Review pending. No claim-level conclusions are implied.</div>'
    body+='<div class="callout">'+E(r['assessment'])+'</div><div class="badges">'+''.join(badge(v,n) for v,n in u['counts'].items())+'</div>'
    if r.get('excerpt_of'):
        body+='<div class="note"><b>Excerpt of a longer episode.</b> <a href="index.html#episode/'+E(r['excerpt_of'])+'">Read the full review and claim-level evidence →</a><p>This listing is accounted for without counting the same claims a second time.</p></div>'
    body+='<details><summary>Source version, speaker attribution and transcript cautions</summary><p>'+E(u.get('date_note'))+'</p><p>'+E(u['transcript']['transcript_type'] if u['transcript'] else 'Source not captured')+'</p><p>'+E(r.get('speaker_map_notes'))+'</p>'+ul(r.get('transcript_cautions',[]))+'<p class="small mono">SHA-256: '+E(r['transcript_sha256'])+'</p></details>'
    body+='<p class="meta">Reviewed version: <a target="_blank" rel="noopener" href="'+E(u['reviewed_version_url'])+'">'+E(u['transcript'].get('platform','Source'))+' · '+E(str(u['transcript'].get('published_at',''))[:10])+'</a></p>'
    if r.get('recording_date') or r.get('recorded_date'):body+='<p class="meta">Stated recording date: '+E(r.get('recording_date') or r.get('recorded_date'))+'</p>'
    body+='<h2 class="section-space">Material claims</h2>'+''.join(claim_html(c,u) for c in r['claims'])
    body+='<h2 class="section-space">How he reasons here</h2>'+ul(r.get('framework_points',[]))+'<h2>Tools and charts discussed</h2><p class="small muted">Mentioned in the transcript; visual charts have not all been inspected.</p>'+ul(r.get('tools_and_charts',[]))
    return body

css=(ROOT/'assets/style.css').read_text()
def shell(title,body,script=''):
    return '<!doctype html>\n<!-- Generated by scripts/build_report.py. Edit source data or templates and rebuild. -->\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><title>'+E(title)+'</title><style>'+css+'</style></head><body><div class="wrap"><header class="topbar"><a class="brand" href="index.html">STEVE EISMAN / RESEARCH AUDIT</a><span class="context">Evidence cutoff · 10 November 2026</span><button class="theme-toggle" aria-label="Toggle dark theme">Dark theme</button></header>'+body+'<footer>Original analysis of The Real Eisman Playbook. This audit is independent of Steve Eisman. Claim counts are not an accuracy percentage. Sources and evidence remain linked.</footer></div><script>const themeButton=document.querySelector(".theme-toggle");function setTheme(d){document.body.classList.toggle("dark",d);themeButton.textContent=d?"Light theme":"Dark theme";try{localStorage.setItem("eisman-theme",d?"dark":"light")}catch(e){}}try{setTheme(localStorage.getItem("eisman-theme")==="dark")}catch(e){}themeButton.onclick=()=>setTheme(!document.body.classList.contains("dark"));</script>'+script+'</body></html>'

claim_to_unit={c['id']:c['unit_id'] for c in allclaims}
claim_by_id={c['id']:c for c in allclaims}
def refs_html(refs):
    links=[]
    for cid in refs:
        if cid not in claim_by_id:continue
        c=claim_by_id[cid]
        label=c['date']+' · '+c['claim'][:90]+('…' if len(c['claim'])>90 else '')
        links.append('<a class="evidence-ref" title="'+E(c['claim'])+'" href="#episode/'+E(c['unit_id'])+'/'+E(cid)+'">'+E(label)+' ↗</a>')
    return '<div class="source-list">'+''.join(links)+'</div>'

def synthesis_block(key,title):
    block=synthesis.get(key)
    if not block:return '<section class="prose"><h2>'+E(title)+'</h2><p>The full-archive synthesis is in progress. Individual completed reviews are available below.</p></section>'
    body='<h2>'+E(title)+'</h2>'+prose(block.get('introduction'))
    if key=='framework':body+='<div class="flow flow-wide">'+(ROOT/'assets/framework.svg').read_text()+'</div><div class="flow flow-narrow">'+(ROOT/'assets/framework-mobile.svg').read_text()+'</div>'
    for section in block.get('sections',[]):
        body+='<section class="synthesis-section"><h3>'+E(section['title'])+'</h3>'+prose(section.get('text'))+ul(section.get('bullets',[]))+refs_html(section.get('claim_ids',[]))+'</section>'
    return body

methodbody='<div class="prose"><h2>Scope and method</h2>'+prose(method['scope'])+prose(method['materiality'])+'<h3>What the verdicts mean</h3><dl>'+''.join('<dt>'+badge(k)+'</dt><dd>'+E(v)+'</dd>' for k,v in method['verdicts'].items())+'</dl><h3>Evaluation rules</h3><ol>'+''.join('<li>'+E(v)+'</li>' for v in method['rules'])+'</ol><h3>Source handling</h3>'+prose(method['source_handling'])+prose(method['local_transcription'])+'<h3>Independent methodology review</h3>'+prose(method['external_review'])+'<h3>Limits</h3>'+ul(method['limits'])+'</div>'
listingrows=''.join('<tr><td>'+E(x['platform'])+'</td><td>'+E(x['published_at'][:10])+'</td><td><a target="_blank" rel="noopener" href="'+E(x['url'])+'">'+E(x['title'])+'</a></td><td><a href="#episode/'+E(x['review_unit_id'])+'">'+E(x['review_unit_id'])+'</a></td></tr>' for x in sorted(catalog['listings'],key=lambda x:x['published_at'],reverse=True))
coverage='<h2>Every listing accounted for</h2><p>'+str(len(catalog['listings']))+' original listings map to '+str(len(units))+' review items. Reposts and cross-platform copies do not create independent forecast successes.</p><p class="small muted">'+E(catalog['scope'])+'</p><div class="filters"><input type="search" id="listing-search" aria-label="Search source listings" placeholder="Search all titles, platforms or IDs"></div><div class="table-wrap"><table id="listing-table"><thead><tr><th>Platform</th><th>Listed date</th><th>Original source</th><th>Review item</th></tr></thead><tbody>'+listingrows+'</tbody></table></div>'
completed=sum(bool(u['review']) for u in units)
body='<section class="hero"><div class="eyebrow">The Real Eisman Playbook · 2025-2026</div><h1>Steve Eisman,<br>one claim at a time.</h1><p>An episode-by-episode scorecard, the strongest and weakest material takes, and a practical guide to how he approaches an investment question.</p></section><section class="stats"><div class="stat"><strong>'+str(len(catalog['listings']))+'</strong>source listings</div><div class="stat"><strong>'+str(completed)+' / '+str(len(units))+'</strong>review items completed</div><div class="stat"><strong>'+f'{len(allclaims):,}'+'</strong>material claim occurrences</div><div class="stat"><strong>6</strong>verdict categories</div></section>'
if completed<len(units):body+='<div class="note"><b>Work in progress.</b> The final synthesis and remaining reviews are unfinished. Coverage is shown explicitly; no complete-archive conclusion is claimed.</div>'
body+='<div class="note">A guest claim is not automatically Eisman’s view. Repeated warnings are not independent wins. A correct business mechanism, a profitable trade and a correctly timed forecast are different tests.</div>'
tabs=[('summary','Summary'),('takes','Best & worst'),('repeated','Repeated points'),('framework','How Eisman thinks'),('library','Episode reviews'),('claims','Claim scorecard'),('tools','Tools & charts'),('method','Method'),('coverage','Coverage')]
body+='<nav class="main-nav" aria-label="Research sections">'+''.join('<a href="#'+k+'" data-panel="'+k+'">'+l+'</a>' for k,l in tabs)+'</nav><main>'
for key,title in [('summary','What to take from Eisman'),('takes','Best and worst material takes'),('repeated','The points he keeps returning to'),('framework','How would Eisman think about this?'),('tools','The analytical toolkit')]:
    body+='<section class="panel" id="'+key+'"'+(' hidden' if key!='summary' else '')+'>'+synthesis_block(key,title)+'</section>'
body+='<section class="panel" id="library" hidden><h2>Read an episode review</h2><div class="filters"><input id="episode-search" type="search" aria-label="Search episode reviews" placeholder="Search episode titles, summaries or claim language"><select id="episode-year" aria-label="Episode year"><option value="">All years</option><option>2026</option><option>2025</option></select><select id="episode-status" aria-label="Review status"><option value="">All review items</option><option value="complete">Reviewed</option><option value="pending">Pending</option></select></div><p class="result-count" id="episode-count" aria-live="polite"></p><div class="grid" id="episode-results"></div></section>'
body+='<section class="panel" id="claims" hidden><h2>Inspect the scorecard</h2><p class="measure muted">Default: Eisman’s own statements. Include guests to audit the whole conversation. Counts describe occurrences, not independent predictions.</p><div class="filters"><input id="claim-search" type="search" aria-label="Search claims" placeholder="Search claims, companies, reasoning or evidence"><select id="speaker-filter" aria-label="Speaker filter"><option value="host">Eisman’s statements</option><option value="guest">Guests & reported views</option><option value="all">All speakers</option></select><select id="verdict-filter" aria-label="Verdict filter"><option value="">All verdicts</option>'+''.join('<option value="'+k+'">'+v+'</option>' for k,v in labels.items())+'</select><select id="materiality-filter" aria-label="Materiality filter"><option value="">All material claims</option><option value="major">Major theses & explanations</option><option value="supporting">Supporting premises</option></select><select id="kind-filter" aria-label="Claim type"><option value="">All claim types</option>'+''.join('<option>'+E(k)+'</option>' for k in sorted({c['kind'] for c in allclaims}))+'</select><select id="claim-year" aria-label="Claim year"><option value="">All years</option><option>2026</option><option>2025</option></select></div><p class="result-count" id="claim-count" aria-live="polite"></p><div id="claim-results"></div><button id="show-more" hidden>Show 50 more</button></section>'
body+='<section class="panel" id="method" hidden>'+methodbody+'</section><section class="panel" id="coverage" hidden>'+coverage+'</section><section class="panel" id="episode" hidden><a href="#library">← Episode library</a><div id="episode-content"></div><p><a href="#library">← Episode library</a></p></section></main>'
payload={'units':units,'claims':allclaims,'labels':labels,'episode_html':{u['id']:episode_body(u) for u in units}}
safe=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
script='<script id="audit-data" type="application/json">'+safe+'</script><script>'+ (ROOT/'assets/app.js').read_text()+'</script>'
(OUT/'index.html').write_text(shell('Steve Eisman | Research scorecard',body,script))
(OUT/'audit-data.json').write_text(json.dumps({k:v for k,v in payload.items() if k!='episode_html'},ensure_ascii=False,indent=2)+'\n')

for u in units:
    (OUT/f'{u["id"]}.html').write_text(shell(u['title']+' | Eisman audit','<main class="article-body"><p class="section-space"><a href="index.html#library">← Research library</a></p>'+episode_body(u)+'</main>'))
    r=u['review']
    lines=['<!-- Generated by scripts/build_report.py. Edit data/reviews or source templates and rebuild. -->','',f'# {u["title"]}','',f'First listed: {u["first_listed_publication"][:10]} | Evaluation cutoff: {method["cutoff"]}','', '[Back to library](../README.md)','']
    lines+=['## Source versions','']+[f'- [{x["platform"]}: {x["title"]}]({x["url"]}) - {x["published_at"][:10]}' for x in u['listings']]+['',u['date_note'],'']
    if r:
        lines+=['## Summary','',r['summary'],'',r['assessment'],'','## Material claims','']
        if r.get('excerpt_of'):lines += [f'This is an excerpt. [Read the full parent review and claim-level evidence]({r["excerpt_of"]}.md). Its repeated claims are not counted again.','']
        for c in r['claims']:
            lines += [f'<a id="{c["id"]}"></a>',f'### {c["id"].rsplit("-c",1)[-1]}. {c["claim"]}','',f'**{labels[c["verdict"]]}** | {c["speaker"]} | {c["kind"]} | {c.get("materiality","not classified")}','',f'[Source at {location(c,u)}]({source_href(c,u)}) | Stance: {c.get("stance","unspecified")} | Horizon: {c.get("horizon","not stated")}','',c['reason'],'']
            if c.get('qualifications'):lines += ['Qualification: '+c['qualifications'],'']
            if c.get('proof'):lines+=['Conditional reasoning: '+(c['proof'].get('derivation','') if isinstance(c['proof'],dict) else str(c['proof'])),'']
            lines += ['Assessment test: '+str(c.get('test') or 'Not specified'),'']
            if followup(c):lines += ['Further verification: '+followup(c),'']
            for e in c.get('evidence',[]):lines += [f'- [{e.get("title") or e.get("publisher") or "Evidence"}]({e["url"]}) ({e.get("date","date unspecified")}): {e.get("finding","")}']
            lines+=['']
        lines+=['## Framework and tools','']+['- '+x for x in r.get('framework_points',[])]+['','Tools and charts discussed, not a complete visual inspection:','']+['- '+x for x in r.get('tools_and_charts',[])]+['','## Source cautions','',r.get('speaker_map_notes','')]+['- '+x for x in r.get('transcript_cautions',[])]+['',f'Transcript SHA-256: `{r["transcript_sha256"]}`','']
    else:lines+=['Review pending.','']
    (MD/f'{u["id"]}.md').write_text('\n'.join(lines).rstrip()+'\n')

for key,title,file in [('summary','Steve Eisman: overall summary','SUMMARY.md'),('takes','Steve Eisman: best and worst material takes','BEST-AND-WORST.md'),('repeated','Steve Eisman: repeated points','REPEATED-POINTS.md'),('framework','How would Steve Eisman think?','FRAMEWORK.md'),('tools','Steve Eisman: tools and charts','TOOLS-AND-CHARTS.md')]:
    b=synthesis.get(key,{})
    lines=['<!-- Generated by scripts/build_report.py. Edit data/synthesis.json and rebuild. -->','',f'# {title}','','[Back to library](README.md)','',f'Evidence cutoff: {method["cutoff"]}.','']
    intro=b.get('introduction', 'Full-archive synthesis in progress.')
    for paragraph in intro if isinstance(intro,list) else [intro]:lines += [paragraph,'']
    for section in b.get('sections',[]):
        lines+=['## '+section['title'],'']
        t=section.get('text',[])
        for paragraph in t if isinstance(t,list) else [t]:lines += [paragraph,'']
        lines+=['- '+v for v in section.get('bullets',[])]+['']
        for ref in section.get('claim_ids',[]):
            if ref in claim_to_unit:lines+=[f'- [Claim {ref}](episodes/{claim_to_unit[ref]}.md#{ref})']
        lines+=['']
    (ROOT/file).write_text('\n'.join(lines).rstrip()+'\n')

methodlines=['<!-- Generated by scripts/build_report.py. Edit data/methodology.json and rebuild. -->','','# Methodology','','[Back to library](README.md)','',method['scope'],'',method['materiality'],'','## Verdicts','']
methodlines+=['- **'+labels[k]+':** '+v for k,v in method['verdicts'].items()]
methodlines+=['','## Rules','']+[f'{i}. {v}' for i,v in enumerate(method['rules'],1)]
methodlines+=['','## Source handling','',method['source_handling'],'',method['local_transcription'],'','## Independent methodology review','',method['external_review'],'','## Limits','']+['- '+v for v in method['limits']]+['']
(ROOT/'METHODOLOGY.md').write_text('\n'.join(methodlines).rstrip()+'\n')
coverage_lines=['<!-- Generated by scripts/build_report.py. Edit data/catalog.json and rebuild. -->',
    '', '# Archive coverage', '', '[Back to library](README.md)', '',
    f'{len(catalog["listings"])} platform listings map to {len(units)} review items: '+
    f'{sum(u["format"]!="excerpt" for u in units)} non-excerpt items and '+
    f'{sum(u["format"]=="excerpt" for u in units)} clips. {completed} review items are complete.',
    '', catalog['scope'], '',
    'Cross-platform matching uses title, topic, guest and release context. It does not establish full transcript equivalence. Dates below are the platform-listed dates; claim locations refer to the version identified inside each review.',
    '', '| Platform | Listed date | Source listing | Review |', '| --- | --- | --- | --- |']
for row in sorted(catalog['listings'],key=lambda x:x['published_at'],reverse=True):
    title=row['title'].replace('|','\\|').replace('[','\\[').replace(']','\\]')
    coverage_lines.append(f'| {row["platform"]} | {row["published_at"][:10]} | [{title}]({row["url"]}) | [Read](episodes/{row["review_unit_id"]}.md) |')
(ROOT/'COVERAGE.md').write_text('\n'.join(coverage_lines).rstrip()+'\n')
print(f'Built {len(units)} pages, {completed} completed reviews, {len(allclaims)} claims.')
