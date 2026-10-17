"""v0.6.16: conservative semantic comparison diagnostics.

Character n-gram similarity is NOT semantic equivalence or contradiction.
Semantic labels beyond exact text identity require separate evidence/review.
"""
import re

SEMANTIC_LABELS=("EXACT_MATCH","SEMANTICALLY_EQUIVALENT","COMPLEMENTARY",
                 "CONTRADICTORY","UNDETERMINED")

def bigrams(text):
    clean=re.sub(r"[\s。、,.!?！？:：;；「」『』（）()\[\]{}]","",text or "").lower()
    if not clean:return set()
    if len(clean)<2:return {clean}
    return {clean[i:i+2] for i in range(len(clean)-1)}

def compare_answers(generated,retrieved):
    if not isinstance(generated,str):raise TypeError("generated must be text")
    if retrieved is not None and not isinstance(retrieved,str):
        raise TypeError("retrieved must be text or null")
    if retrieved is None or not retrieved.strip():
        return {"semantic_label":"UNDETERMINED","reason":"NO_RETRIEVAL",
                "character_bigram_jaccard":None,"model_verification":False,
                "requires_human_review":True}
    a=generated.strip();b=retrieved.strip()
    ga=bigrams(a);rb=bigrams(b)
    score=len(ga&rb)/len(ga|rb) if (ga|rb) else 1.0
    exact=a==b and bool(a)
    return {"semantic_label":"EXACT_MATCH" if exact else "UNDETERMINED",
            "reason":"EXACT_TEXT_MATCH" if exact else "TEXT_DIFFERENCE_NOT_SEMANTIC_JUDGMENT",
            "character_bigram_jaccard":round(score,6),
            "model_verification":False,"requires_human_review":True}
