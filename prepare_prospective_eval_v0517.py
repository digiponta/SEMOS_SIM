"""v0.5.17 independent evaluation manifest validator (no model training).
Create a manifest *before* any prospective evaluation. This utility does not
create new gold-labeled examples and never estimates classification accuracy.
"""
import argparse,csv,hashlib,json
from pathlib import Path

LABELS={"VM-A","VM-B","VM-C","UNKNOWN"}
FIELDS=("request_id","text","gold","subject","predicate","object","intent","topic_group","source_id")
def digest(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for block in iter(lambda:f.read(65536),b""):h.update(block)
 return h.hexdigest()
def normalize(text):return " ".join(text.casefold().split())
def inspect(path,prior_texts=()):
 seen=set();duplicate=[];missing=[];overlap=[];topic=set();source=set()
 prior={normalize(t) for t in prior_texts}
 with open(path,encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  if not reader.fieldnames or set(FIELDS)-set(reader.fieldnames):
   raise ValueError("CSV requires columns: "+", ".join(FIELDS))
  counts={label:0 for label in sorted(LABELS)}
  for index,row in enumerate(reader,2):
   ident=row["request_id"].strip();raw=row["text"].strip()
   if not ident or not raw or not row["topic_group"].strip() or not row["source_id"].strip():
    missing.append(index)
   key=normalize(raw)
   if key in seen:duplicate.append(index)
   seen.add(key)
   if key in prior:overlap.append(index)
   label=row["gold"].strip()
   if label not in LABELS:raise ValueError("Invalid gold label at line "+str(index))
   counts[label]+=1;topic.add(row["topic_group"].strip());source.add(row["source_id"].strip())
 return {"rows":sum(counts.values()),"label_counts":counts,
         "topics":len(topic),"sources":len(source),
         "duplicate_lines":duplicate,"prior_development_overlap_lines":overlap,
         "missing_required_lines":missing,
         "structured_coverage":{}, "valid_structure":not(duplicate or overlap or missing)}
def load_existing(path):
 doc=json.loads(Path(path).read_text(encoding="utf-8-sig"))
 return [r["text"] for r in doc["rows"]]
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--prospective",required=True)
 p.add_argument("--development-trace",default="results/nested_traces_v0511.json")
 p.add_argument("--output",default="results/prospective_manifest_v0517.json")
 args=p.parse_args()
 src=Path(args.prospective);out=Path(args.output)
 if out.exists():p.error("Refusing overwrite")
 if not src.is_file():p.error("Prospective CSV does not exist")
 prior=load_existing(args.development_trace)
 result={"version":"0.5.17","kind":"PROSPECTIVE_DATASET_MANIFEST",
         "dataset_sha256":digest(src),
         "development_trace_sha256":digest(args.development_trace),
         "schema":list(FIELDS),"audit":inspect(src,prior),
         "limitations":["Does not establish topic independence or provenance authenticity",
                       "Normalized exact text overlap only; paraphrase leakage not detected",
                       "No model or routing evaluation performed",
                       "Prospective dataset must be authored independently and frozen before testing",
                       "Not a 2 Copies in 3 synchronization test"]}
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
 print("Valid structure:",result["audit"]["valid_structure"])
 print("Rows:",result["audit"]["rows"],"Overlap:",len(result["audit"]["prior_development_overlap_lines"]))
 print("Saved:",out)
if __name__=="__main__":main()
