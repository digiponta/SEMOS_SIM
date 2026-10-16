"""Review new retry answers from v0.5.29.4, without preapproving them.

Tkinter GUI writes a new round-specific CSV for subsequent replay through the
v0.5.29.3 decision-file mechanism; it does NOT execute another VM.
"""
import argparse,csv,json,tkinter as tk
from pathlib import Path
from tkinter import ttk,messagebox

CHOICES=("APPROVE","REJECT","RETRY","DISCOVERY")
def pending_rows(doc):
    return [x for x in doc["packets"] if x.get("status")=="PENDING_USER_REVIEW"
            and x.get("provenance") and x.get("answer") and x.get("question")]

def save(path,decisions):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+".tmp")
    with temp.open("w",encoding="utf-8",newline="") as f:
        writer=csv.writer(f);writer.writerow(("request_id","decision"))
        for rid,choice in sorted(decisions.items()):
            if choice not in CHOICES:raise ValueError("Invalid decision")
            writer.writerow((rid,choice))
    temp.replace(path)

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--input",default="results/hitl_retry_validated_v05294.json")
    a.add_argument("--output",default="data/hitl_retry_review_v05294.csv")
    args=a.parse_args()
    doc=json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    if doc.get("version")!="0.5.29.4":a.error("Expected v0.5.29.4")
    rows=pending_rows(doc)
    if not rows:a.error("No validated pending answers to review")
    if Path(args.output).exists():a.error("Refusing to overwrite existing reviews")
    root=tk.Tk();root.title("SEMOS_SIM 0.5.29.4 再回答レビュー");root.geometry("960x680")
    frame=ttk.Frame(root,padding=16);frame.pack(fill="both",expand=True)
    top=ttk.Label(frame,font=("",12,"bold"));top.pack(anchor="w")
    provenance=ttk.Label(frame,wraplength=900);provenance.pack(anchor="w",pady=(6,12))
    ttk.Label(frame,text="質問").pack(anchor="w")
    question=tk.Text(frame,height=5,wrap="word");question.pack(fill="x")
    ttk.Label(frame,text="再回答（ユーザー未承認）").pack(anchor="w",pady=(12,0))
    answer=tk.Text(frame,height=12,wrap="word");answer.pack(fill="both",expand=True)
    position=[0];decisions={}
    def update():
        row=rows[position[0]]
        top.config(text=f"{position[0]+1}/{len(rows)} | {row['request_id']} | {row['vm']} | {decisions.get(row['request_id'],'未判断')}")
        meta=row["provenance"]
        provenance.config(text=f"自己申告の出所: {meta['source']} | 実行ID: {meta['execution_id']} | 時刻: {meta['executed_at']} | 出所未検証")
        for widget,s in ((question,row["question"]),(answer,row["answer"])):
            widget.config(state="normal");widget.delete("1.0","end");widget.insert("1.0",s);widget.config(state="disabled")
    def choose(choice):
        row=rows[position[0]]
        if not messagebox.askyesno("確認",f"{row['request_id']} の再回答を {choice} と記録しますか？"):return
        decisions[row["request_id"]]=choice
        save(args.output,decisions)
        position[0]=(position[0]+1)%len(rows);update()
    controls=ttk.Frame(frame);controls.pack(fill="x",pady=10)
    for choice,jp in (("APPROVE","承認"),("REJECT","拒否"),("RETRY","別VM"),("DISCOVERY","Discovery")):
        ttk.Button(controls,text=jp,command=lambda c=choice:choose(c)).pack(side="left",padx=6)
    def step(inc):position[0]=(position[0]+inc)%len(rows);update()
    ttk.Button(controls,text="前へ",command=lambda:step(-1)).pack(side="right")
    ttk.Button(controls,text="次へ",command=lambda:step(1)).pack(side="right")
    update();root.mainloop()
if __name__=="__main__":main()
