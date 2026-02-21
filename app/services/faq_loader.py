import json

def load_faqs(path="data/hit_faq_rag.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)