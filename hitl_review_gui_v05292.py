"""SEMOS_SIM v0.5.29.2 — local Tkinter HITL review GUI.

Requires real question/answer CSV. No invented VM responses. Decisions are
saved to a separate CSV, never taken without a button click. This is NOT a VM
runtime; RETRY is a handoff for later processing only.
"""
import argparse,csv,json,tkinter as tk
from pathlib import Path
from tkinter import messagebox,ttk
from prepare_hitl_packets_v05291 import read_payload,review
from simulate_hitl_review_v0529 import load_reviews

DECISIONS=("APPROVE","REJECT","RETRY","DISCOVERY")

def reviewable(records,payloads):
    return [r for r in records if r["final"]!="DISCOVERY" and r["request_id"] in payloads
            and str(payloads[r["request_id"]].get("question","")).strip()
            and str(payloads[r["request_id"]].get("answer","")).strip()]

def save_decisions(path,decisions):
    dest=Path(path);dest.parent.mkdir(parents=True,exist_ok=True)
    # overwrite atomically to reduce partial file risk
    tmp=dest.with_name(dest.name+".tmp")
    with tmp.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["request_id","decision"])
        for rid,choice in sorted(decisions.items()):
            if choice not in DECISIONS:raise ValueError("Invalid review choice")
            w.writerow([rid,choice])
    tmp.replace(dest)

class ReviewWindow:
    def __init__(self,root,records,payloads,decisions,output):
        self.root=root;self.records=records;self.payloads=payloads
        self.decisions=decisions;self.output=output;self.index=0
        root.title("SEMOS_SIM v0.5.29.2 — User Answer Review")
        root.geometry("940x700")
        main=ttk.Frame(root,padding=16);main.pack(fill="both",expand=True)
        self.header=ttk.Label(main,font=("",13,"bold"));self.header.pack(anchor="w")
        self.progress=ttk.Label(main);self.progress.pack(anchor="w",pady=(4,12))
        ttk.Label(main,text="ユーザーの質問").pack(anchor="w")
        self.question=tk.Text(main,height=6,wrap="word",state="disabled")
        self.question.pack(fill="x",pady=(3,12))
        ttk.Label(main,text="VMの回答（仮回答・未確定）").pack(anchor="w")
        self.answer=tk.Text(main,height=12,wrap="word",state="disabled")
        self.answer.pack(fill="both",expand=True,pady=(3,12))
        self.info=ttk.Label(main,wraplength=900);self.info.pack(anchor="w",pady=(0,10))
        actions=ttk.Frame(main);actions.pack(fill="x")
        for choice,label in (("APPROVE","承認"),("REJECT","拒否"),
                             ("RETRY","別VMへ"),("DISCOVERY","Discovery")):
            ttk.Button(actions,text=label,command=lambda c=choice:self.choose(c)).pack(side="left",padx=(0,8))
        nav=ttk.Frame(main);nav.pack(fill="x",pady=(14,0))
        ttk.Button(nav,text="前へ",command=lambda:self.move(-1)).pack(side="left")
        ttk.Button(nav,text="次へ",command=lambda:self.move(1)).pack(side="left",padx=8)
        ttk.Button(nav,text="保存",command=self.persist).pack(side="right")
        self.render()
    def set_text(self,widget,value):
        widget.config(state="normal")
        widget.delete("1.0","end");widget.insert("1.0",value);widget.config(state="disabled")
    def render(self):
        if not self.records:
            self.header.config(text="レビュー可能なVM回答がありません")
            self.progress.config(text="質問文と回答本文をCSVで指定してください")
            return
        rec=self.records[self.index];rid=rec["request_id"];payload=self.payloads[rid]
        current=self.decisions.get(rid,"未判断")
        self.header.config(text=f"{rid} | {rec['final']} | PROVISIONAL_RESULT")
        self.progress.config(text=f"{self.index+1}/{len(self.records)}  判定: {current}")
        self.set_text(self.question,payload["question"])
        self.set_text(self.answer,payload["answer"])
        previous=[e.get("vm") for e in rec.get("events",[]) if e.get("state") in ("DISPATCH","CAPABILITY_PROBE")]
        self.info.config(text=f"訪問済みVM: {', '.join(previous) or rec['final']}  ／  回答は事実確認済みとは限りません")
    def move(self,delta):
        if self.records:self.index=(self.index+delta)%len(self.records);self.render()
    def persist(self):
        try:save_decisions(self.output,self.decisions)
        except OSError as exc:messagebox.showerror("保存エラー",str(exc));return
        messagebox.showinfo("保存",f"判断結果を保存しました:\n{self.output}")
    def choose(self,choice):
        if not self.records:return
        rec=self.records[self.index];rid=rec["request_id"]
        # Review engine guards all decisions, and retry is only a handoff.
        try:result=review(rec,choice,self.payloads[rid])
        except ValueError as exc:messagebox.showerror("検証エラー",str(exc));return
        message=f"{rid}: {choice}\n状態: {result['status']}\n"
        if choice=="RETRY":message+="再配送先は次工程で決定・実行されます。"
        if not messagebox.askyesno("判断の確認",message+"\nこの判断を記録しますか？"):return
        self.decisions[rid]=choice
        try:save_decisions(self.output,self.decisions)
        except OSError as exc:
            del self.decisions[rid];messagebox.showerror("保存エラー",str(exc));return
        self.move(1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/user_authorized_rr_v0526.json")
    p.add_argument("--payload-file",required=True)
    p.add_argument("--review-file",default="data/hitl_gui_decisions_v05292.csv")
    a=p.parse_args()
    doc=json.loads(Path(a.input).read_text(encoding="utf-8-sig"))
    if doc.get("version")!="0.5.26":p.error("Requires v0.5.26 routing records")
    records=doc["records"];payloads=read_payload(a.payload_file)
    ids={r["request_id"] for r in records}
    if set(payloads)-ids:p.error("Payload contains unknown request IDs")
    review_file=Path(a.review_file)
    decisions=load_reviews(review_file) if review_file.exists() else {}
    if set(decisions)-ids:p.error("Review has unknown request IDs")
    active=reviewable(records,payloads)
    if set(decisions)-{r["request_id"] for r in active}:
        p.error("Review file includes a request without reviewable answer")
    root=tk.Tk();ReviewWindow(root,active,payloads,decisions,review_file);root.mainloop()
if __name__=="__main__":main()
