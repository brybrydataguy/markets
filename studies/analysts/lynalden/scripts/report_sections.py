"""Summary, framework and chart-reading components for the research report."""
from pathlib import Path
from collections import Counter
import html
esc=lambda x:html.escape(str(x))
EXTRA_CSS='''
.summary-lead{font-size:clamp(25px,3vw,38px);line-height:1.32;max-width:1100px;margin:0 0 28px}.summary-copy{columns:2;column-gap:38px;max-width:1200px}.summary-copy p{break-inside:avoid;font-size:18px}.dimension{border-top:3px solid var(--blue)}.dimension .judgment{color:var(--blue);font:600 13px system-ui;margin-bottom:13px}.episode-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.episode-grid>*{min-width:0}.episode .meta{color:var(--blue);margin-bottom:12px}.section-space{margin-top:48px}.chart-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.chart-card{background:var(--paper);border:1px solid var(--line);padding:22px;min-width:0}.chart-card img{display:block;width:100%;height:auto;background:white;margin:14px 0;border:1px solid var(--line)}.chart-card p{font-size:16px}.chart-card h3{margin:0}.chart-card .meta{margin-top:7px}.chart-card details{margin-top:8px}.framework-diagram{display:block;width:100%;max-width:1100px;margin:28px 0 38px}.mobile-diagram{display:none}.example-tabs{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}.example-tabs button{font:14px system-ui;text-align:left}.example-tabs button[aria-selected=true]{background:var(--pale);border-color:var(--blue);color:var(--blue)}.worked-example{padding:25px;border:1px solid var(--line);background:var(--paper)}.worked-example[hidden]{display:none}.worked-example li{margin:8px 0}.distribution td:not(:first-child),.distribution th:not(:first-child){text-align:right;font-variant-numeric:tabular-nums}.download-link{display:inline-block;margin:12px 0;font:14px system-ui}.report-status{font:13px system-ui;color:var(--muted)}
@media(max-width:600px){.desktop-diagram{display:none}.mobile-diagram{display:block}}
@media(max-width:800px){.summary-copy{columns:1}.episode-grid,.chart-grid{grid-template-columns:minmax(0,1fr)}}
'''
def links(ids):
 return '<div class="source-list">'+''.join(f'<a href="article-{esc(i)}.html">Report {esc(i)}</a>' for i in ids)+'</div>'

def summary_section(syn,claims,reviews,labels):
 s=syn['summary'];body='<section class="panel" id="summary"><h2>The overall assessment</h2><p class="summary-lead">'+esc(s['headline'])+'</p>'
 body+='<div class="summary-copy">'+''.join('<p>'+esc(p)+'</p>' for p in s['paragraphs'])+'</div>'
 body+='<div class="grid section-space">'+''.join('<article class="card dimension"><h3>'+esc(x['name'])+'</h3><div class="judgment">'+esc(x['judgment'])+'</div><p>'+esc(x['text'])+'</p>'+links(x['article_ids'])+'</article>' for x in s['dimensions'])+'</div>'
 body+='<h2 class="section-space">The major episodes</h2><p class="measure muted">These are selected, consequential episodes from the full claim library, not a statistically independent sample or an exhaustive episode count. The links preserve the original entries, revisions and counterexamples.</p><div class="episode-grid">'
 for x in syn.get('episodes',[]):
  body+='<article class="card episode"><div class="meta">'+esc(x['outcome'])+'</div><h3>'+esc(x['title'])+'</h3><p>'+esc(x['text'])+'</p>'+links(x['article_ids'])+'</article>'
 body+='</div><h2 class="section-space">What the verdict counts contain</h2><p class="measure muted">Counts below are repeated claim occurrences, including descriptions and explanations. They cannot be read as an accuracy rate. “Evidence needed” is an audit gap; “too early” means an actual future horizon remains.</p><div class="table-wrap"><table class="distribution"><thead><tr><th>Type</th>'+''.join('<th>'+esc(v)+'</th>' for v in labels.values())+'<th>Total</th></tr></thead><tbody>'
 for kind,title in [('forecast','Forecast'),('investment_thesis','Investment thesis'),('explanation','Explanation'),('empirical','Empirical assertion')]:
  counts=Counter(c['verdict'] for c in claims if c['kind']==kind)
  body+='<tr><td>'+title+'</td>'+''.join('<td>'+str(counts.get(v,0))+'</td>' for v in labels)+'<td>'+str(sum(counts.values()))+'</td></tr>'
 body+='</tbody></table></div><p class="small muted">Coverage: '+str(len(reviews))+' of 200 article reviews available. Each review links its evidence and explains its limits. Market sensitivities use stated windows and adjusted-price proxies, not a reconstructed model-portfolio track record.</p><a class="download-link" href="audit-data.json" download>Download the local structured scorecard (JSON)</a></section>'
 return body

def framework_diagram():
 desktop='''<svg class="framework-diagram desktop-diagram" viewBox="0 0 1080 340" role="img" aria-labelledby="frame-title frame-desc"><title id="frame-title">From economic regime to an investable thesis</title><desc id="frame-desc">First map the regime, balance sheets and constraints. Then test value capture, price and the investment expression. Update the thesis against a written failure condition.</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="var(--blue)"/></marker></defs><g fill="var(--paper)" stroke="var(--line)"><rect x="2" y="25" width="325" height="105" rx="3"/><rect x="377" y="25" width="325" height="105" rx="3"/><rect x="752" y="25" width="325" height="105" rx="3"/><rect x="2" y="192" width="325" height="105" rx="3"/><rect x="377" y="192" width="325" height="105" rx="3"/><rect x="752" y="192" width="325" height="105" rx="3"/></g><g stroke="var(--blue)" stroke-width="2" fill="none" marker-end="url(#arrow)"><path d="M337 78H367"/><path d="M712 78H742"/><path d="M915 140V182"/><path d="M742 245H712"/><path d="M367 245H337"/></g><g fill="var(--ink)" font-family="Georgia,serif" font-size="24"><text x="24" y="64">1. Regime and horizon</text><text x="399" y="64">2. Balance sheets</text><text x="774" y="64">3. Binding constraints</text><text x="774" y="231">4. Value capture</text><text x="399" y="231">5. Price and catalyst</text><text x="24" y="231">6. Position and review</text></g><g fill="var(--muted)" font-family="system-ui,sans-serif" font-size="16"><text x="24" y="100">Cycle, fiscal flows, policy limits</text><text x="399" y="100">Currency, maturity, funding</text><text x="774" y="100">Energy, capacity, rules</text><text x="774" y="267">Customer, producer or investor?</text><text x="399" y="267">What is already expected?</text><text x="24" y="267">Vehicle, size, failure condition</text></g></svg>'''

 steps=[('Regime and horizon','Cycle, fiscal flows, policy limits'),('Balance sheets','Currency, maturity, funding'),('Binding constraints','Energy, capacity, rules'),('Value capture','Customer, producer or investor?'),('Price and catalyst','What is already expected?'),('Position and review','Vehicle, size, failure condition')]
 mobile='<svg class="framework-diagram mobile-diagram" viewBox="0 0 360 760" role="img" aria-label="Six steps from regime to investment review">'
 for i,(title,detail) in enumerate(steps):
  y=2+i*130
  mobile+=f'<rect x="2" y="{y}" width="356" height="105" rx="3" fill="var(--paper)" stroke="var(--line)"/><text x="22" y="{y+40}" font-family="Georgia,serif" font-size="22" fill="var(--ink)">{i+1}. {esc(title)}</text><text x="22" y="{y+75}" font-family="system-ui,sans-serif" font-size="15" fill="var(--muted)">{esc(detail)}</text>'
  if i<5:mobile+=f'<path d="M180 {y+111}v12m-4-4l4 4 4-4" fill="none" stroke="var(--blue)" stroke-width="2"/>'
 return desktop+mobile+'</svg>'


def examples_section(syn):
 examples=syn.get('examples',[])
 body='<h2 class="section-space">Apply the framework</h2><p class="measure muted">Reviewer-created examples of the questions this framework suggests. These are not predictions of Lyn’s actual current opinion.</p><div class="example-tabs" role="tablist" aria-label="Framework examples">'
 for i,x in enumerate(examples):body+=f'<button data-example="{i}" role="tab" aria-selected="{str(i==0).lower()}">'+esc(x['title'])+'</button>'
 body+='</div>'
 for i,x in enumerate(examples):
  body+=f'<section class="worked-example" id="example-{i}"'+(' hidden' if i else '')+'><h3>'+esc(x['title'])+'</h3><p>'+esc(x['reading'])+'</p><ul>'+''.join('<li>'+esc(q)+'</li>' for q in x['questions'])+'</ul><div class="note">'+esc(x['caution'])+'</div>'+links(x['article_ids'])+'</section>'
 body+='''<script>document.querySelectorAll('[data-example]').forEach(b=>b.onclick=()=>{document.querySelectorAll('.worked-example').forEach(p=>p.hidden=p.id!=='example-'+b.dataset.example);document.querySelectorAll('[data-example]').forEach(t=>t.setAttribute('aria-selected',String(t===b)))})</script>'''
 return body

def views_section(syn):
 body='<h2 class="section-space">The recurring views</h2><p class="measure muted">These reconstruct positions across the archive, with the period and qualifications kept visible. They are not a prediction of what the author would recommend today.</p><div class="episode-grid">'
 for x in syn.get('views',[]):
  body+='<article class="card"><h3>'+esc(x['view'])+'</h3><p>'+esc(x['description'])+'</p><p><b>Audit qualification:</b> '+esc(x['qualification'])+'</p>'+links(x['article_ids'])+'</article>'
 return body+'</div>'

def charts_section(charts,out):
 body='<h2 class="section-space">Reading the charts critically</h2><p class="measure muted">These chart interpretations were informed by visual inspection during the local audit. Original chart images remain with their publishers; follow the source links to inspect them. Other chart references were inventoried without full visual inspection.</p><div class="chart-grid">'
 for x in charts:
  body+='<article class="chart-card"><h3>'+esc(x['alt'])+'</h3><div class="meta">Report '+esc(x['article_id'])+' · '+esc(x['date'])+'</div><p>'+esc(x['reviewer_note'])+'</p><div class="source-list"><a href="article-'+esc(x['article_id'])+'.html">Read the article review</a><a href="'+esc(x['url'])+'" target="_blank" rel="noopener">Open original chart ↗</a></div></article>'
 return body+'</div>'


def glossary_section():
 terms=[
  ('TGA', 'Treasury General Account: the U.S. government’s account at the Federal Reserve.', 'A rising balance drains bank reserves if other balance-sheet items are unchanged. Offsetting flows matter.'),
  ('Bank reserves', 'Balances eligible banks hold at the central bank for settlement and liquidity.', 'They are distinct from household deposits and are not mechanically lent out to create a fixed amount of credit.'),
  ('Overnight RRP', 'A Fed facility in which eligible counterparties temporarily place cash against securities.', 'A falling balance can offset reserve drains elsewhere. Money funds and banks hold different claims.'),
  ('QT and Fed purchases', 'QT lets securities holdings run down. Purchases add securities and matching liabilities.', 'Reserve-management purchases and monetary easing can differ in purpose and maturity; size alone does not identify the policy stance.'),
  ('Fiscal dominance', 'A setting in which government financing constraints strongly influence monetary policy.', 'It is a hypothesis about constraints and incentives, not proof that rates cannot rise or that every rate hike stimulates growth.'),
  ('Real yields', 'Returns after inflation; TIPS yields provide a market-based real-yield measure.', 'Expected and realized inflation differ. TIPS prices also reflect liquidity and risk premia.'),
  ('Yield curve', 'Interest rates across maturities, often summarized by a long-minus-short spread.', 'Inversion is a warning signal with variable lead times, not a uniquely timed recession forecast.'),
  ('Credit spread', 'The yield difference between risky debt and a comparison instrument.', 'Match maturity and other features. The spread reflects liquidity and risk compensation as well as default expectations.'),
  ('Credit impulse', 'A measure of acceleration or deceleration in new credit, usually scaled to economic output.', 'A slowing impulse can coexist with a growing debt stock. Definitions and currency translation vary.'),
  ('Global M2', 'An aggregation of broad-money measures across countries, often translated into dollars.', 'Country coverage, definitions and exchange rates affect the result. It is not a single globally spendable pool.'),
  ('MVRV', 'Bitcoin market value divided by realized value, which revalues coins when they last moved.', 'Coin movement is not always a purchase. Historical valuation bands are not guaranteed price floors.'),
  ('CAPE', 'Price relative to a long average of inflation-adjusted earnings, commonly ten years.', 'Useful for valuation context; accounting, sector mix and interest rates complicate comparisons and short-term timing.'),
  ('FAST Graphs', 'Charts combining share price, company fundamentals, valuation multiples and estimates.', 'The historical multiple is a reference, and future earnings points are forecasts. Neither is guaranteed fair value.'),
  ('SLR', 'Supplementary leverage ratio: a capital backstop based on total leverage exposure.', 'It differs from risk-weighted capital ratios. Cash reserves, bank capital and Treasury risk weights are different concepts.'),
  ('Capital cycle', 'Investment changes future supply, often with a long delay in physical industries.', 'Low investment can support future returns, but only if demand, costs, access and the selected investment vehicle cooperate.')
 ]
 body='<h2 class="section-space">A plain-language glossary</h2><p class="measure muted">Reviewer explanations of the terms that recur across the archive. The cautions keep the definition separate from a market prediction.</p><div class="table-wrap"><table><thead><tr><th>Term</th><th>Meaning</th><th>What to watch</th></tr></thead><tbody>'
 for name,meaning,caution in terms:
  body+='<tr><td><b>'+esc(name)+'</b></td><td>'+esc(meaning)+'</td><td>'+esc(caution)+'</td></tr>'
 return body+'</tbody></table></div>'
