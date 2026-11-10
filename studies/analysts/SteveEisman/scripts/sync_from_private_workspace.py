"""Import original review prose and safe provenance, never source transcripts."""
import argparse
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('research_root',type=Path)
args=parser.parse_args()
ROOT=Path(__file__).resolve().parent.parent
source=args.research_root.resolve()
catalog=json.loads((source/'acquisition/catalog.json').read_text())
for u in catalog['units']:
    path=source/'reviews'/f'{u["review_source_id"]}.json'
    if path.exists():
        data=json.loads(path.read_text())
        data['source_id']=path.stem
        # Preserve authored claim IDs while standardizing the three review schemas.
        for claim in data['claims']:
            if isinstance(claim.get('proof'),dict) and not claim['proof'].get('derivation'):
                claim['proof']['derivation']=claim['proof'].get('proof','')
            if not claim.get('proof'):
                basis=claim.get('evidence_basis')
                if isinstance(basis,dict) and basis.get('type')=='deductive':
                    claim['proof']={'assumptions':basis.get('assumptions',[]),
                                    'derivation':basis.get('proof') or basis.get('derivation') or claim['reason']}
                elif basis=='deductive':
                    assumptions=claim.get('proof_assumptions',[])
                    claim['proof']={'assumptions':assumptions if isinstance(assumptions,list) else [],
                                    'derivation':claim.get('deductive_proof') or (assumptions if isinstance(assumptions,str) else claim['reason'])}
        # Reviews contain original paraphrases, source locations and evidence.
        for key in ('segments','transcript','raw_text','body_html','body_json','audio_url'):
            if key in data:raise ValueError(f'Private source field {key} in {path.name}')
        rendered=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
        if '\u2014' in rendered:raise ValueError(f'Em dash in authored review {path.name}')
        if any(x in rendered for x in ('?token=','&token=','signature=','access_token=')):
            raise ValueError(f'Access URL in {path.name}')
        (ROOT/'data/reviews'/path.name).write_text(rendered)
        u['review_available']=True
    else:
        u['review_available']=False
(ROOT/'data/catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'Imported {sum(u["review_available"] for u in catalog["units"])} of {len(catalog["units"])} review units.')
