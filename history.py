import os
import json

HISTORY_FILE = "sent_history.json"

def load_sent_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            return set(data.get("sent_ids", []))
    except Exception as e:
        print(f"⚠️ Error loading history file: {e}")
        return set()

def save_sent_history(sent_ids):
    try:
        data = {"sent_ids": list(sent_ids)}
        with open(HISTORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving history file: {e}")

def filter_already_sent(opportunities):
    sent_ids = load_sent_history()
    fresh_opportunities = []
    
    for opp in opportunities:
        opp_id = opp.get("id")
        if opp_id and opp_id in sent_ids:
            continue
        fresh_opportunities.append(opp)
        
    return fresh_opportunities

def mark_as_sent(opportunities):
    sent_ids = load_sent_history()
    for opp in opportunities:
        opp_id = opp.get("id")
        if opp_id:
            sent_ids.add(opp_id)
    save_sent_history(sent_ids)
