import json


def load_profile():
    with open("profile.json", "r", encoding="utf-8") as f:
        return json.load(f)
