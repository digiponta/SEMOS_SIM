"""v0.6.11: compare generated/retrieved answers in HITL without granting approval.

A selection is a review *preference* only, not APPROVE, semantic promotion,
or a finalizer-compatible decision CSV. Writes a separate JSON draft.
"""
import argparse,json,hashlib
from pathlib import Path

CHOICES=("GENERATED","RETRIEVED","REJECT_BOTH","HOLD")
def pending_rows(doc):
    return [p for p in doc.get("packets",[])
      if p.get("status")=="PENDING_USER_REVIEW" and p.get("provenance")
      and isinstance(p.get("evidence_comparison"),dict)]
def choice_record(packet,choice):
    if choice not in CHOICES:raise ValueError("Invalid comparison choice")
    if packet.get("status")!="PENDING_USER_REVIEW":raise ValueError("Not pending review")
    ev=packet.get("evidence_comparison")
    if not isinstance(ev,dict):raise ValueError("Evidence comparison missing")
    gen=ev.get("generated") or {}
    retrieved=ev.get("retrieved") or {}
    if choice=="GENERATED" and not str(gen.get("answer") or "").strip():
        raise ValueError("No generated answer")
    if choice=="RETRIEVED" and (not retrieved.get("present") or not str(retrieved.get("answer") or "").strip()):
        raise ValueError("No retrieved answer")
    return {"request_id":packet["request_id"],"selection":choice,
      "status":"HITL_COMPARISON_SELECTION_ONLY",
      "approved":False,"promoted":False,
      "provenance_verified":False}
def make_report(input_bytes,packets,choices):
    if len({p["request_id"] for p in packets})!=len(packets):
        raise ValueError("Duplicate request IDs")
    ids={p["request_id"] for p in packets}
    if set(choices)-ids:raise ValueError("Unknown request ID")
    by_id={p["request_id"]:p for p in packets}
    return {"version":"0.6.11","kind":"HITL_EVIDENCE_COMPARISON_DRAFT",
      "input_sha256":hashlib.sha256(input_bytes).hexdigest(),
      "selections":[choice_record(by_id[rid],choice) for rid,choice in sorted(choices.items())],
      "limitations":["Not an approval or finalization decision",
       "Does not trigger VM execution, Discovery or Semantic Memory update",
       "Unverified backend provenance; user selection is not fact verification"]}
def save_draft(output,raw,packets,choices):
    dst=Path(output)
    # Create-only, never silently overwrite an existing review.
    data=json.dumps(make_report(raw,packets,choices),ensure_ascii=False,indent=2).encode("utf-8")
    dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open("xb") as f:f.write(data)
def main():
    import tkinter as tk
    from tkinter import ttk,messagebox
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    if Path(a.output).exists():ap.error("Refusing overwrite")
    raw=Path(a.input).read_bytes()
    doc=json.loads(raw.decode("utf-8-sig"))
    rows=pending_rows(doc)
    if not rows:ap.error("No pending evidence-comparison cases")
    root=tk.Tk();root.title("SEMOS_SIM v0.6.11 HITL 根拠比較（選択は未承認）")
    root.geometry("1060x780")
    frame=ttk.Frame(root,padding=14);frame.pack(fill="both",expand=True)
    title=ttk.Label(frame,font=("",12,"bold"));title.pack(anchor="w")
    meta=ttk.Label(frame,wraplength=980);meta.pack(anchor="w",pady=8)
    labels=[]
    for label,height in (("質問",3),("生成回答（LLM）",7),("検索回答（Semantic Knowledge）",7)):
        ttk.Label(frame,text=label).pack(anchor="w")
        w=tk.Text(frame,height=height,wrap="word");w.pack(fill="both",expand=True,pady=(0,8))
        labels.append(w)
    current=[0];choices={}
    def render():
        p=rows[current[0]];e=p["evidence_comparison"]
        g=e.get("generated") or {};ret=e.get("retrieved") or {}
        title.config(text=f"{current[0]+1}/{len(rows)} | {p['request_id']} | {choices.get(p['request_id'],'未選択')}")
        ass=p.get("semantic_assessment") or {}
        meta.config(text=f"比較: {e.get('relation','不明')} | Semantic: {ass.get('state','不明')} | "
                         "出所は自己申告・未検証 | 選択は最終承認ではありません")
        for w,value in zip(labels,[p.get("question",""),g.get("answer") or "(なし)",
                                   ret.get("answer") if ret.get("present") else "(検索ヒットなし)"]):
            w.config(state="normal");w.delete("1.0","end");w.insert("1.0",value or "(なし)");w.config(state="disabled")
    def select(ch):
        p=rows[current[0]]
        try:choice_record(p,ch)
        except ValueError as exc:messagebox.showerror("選択不可",str(exc));return
        if not messagebox.askyesno("記録の確認",f"{p['request_id']}: {ch} を未承認の比較選択として保存しますか？"):return
        updated=dict(choices);updated[p["request_id"]]=ch
        try:save_draft(a.output,raw,rows,updated)
        except FileExistsError:
            messagebox.showerror("保存不可","出力ファイルが既に存在します。新しい --output 名で起動してください。")
            return
        choices.update(updated)
        messagebox.showinfo("保存完了","比較選択をJSONに記録しました。これは承認ではありません。")
        root.destroy()
    controls=ttk.Frame(frame);controls.pack(fill="x")
    for c,label in (("GENERATED","生成回答を選択"),("RETRIEVED","検索回答を選択"),
                    ("REJECT_BOTH","両方拒否"),("HOLD","保留")):
        ttk.Button(controls,text=label,command=lambda x=c:select(x)).pack(side="left",padx=4)
    def move(delta):
        current[0]=(current[0]+delta)%len(rows);render()
    ttk.Button(controls,text="前へ",command=lambda:move(-1)).pack(side="right")
    ttk.Button(controls,text="次へ",command=lambda:move(1)).pack(side="right")
    render();root.mainloop()
if __name__=="__main__":main()
