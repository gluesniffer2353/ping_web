import os
import re
import json
import requests

URL = "https://oeil.europarl.europa.eu/oeil/en/procedure-file?reference=2022%2F0155%28COD%29"
STATE_FILE = "chatcontrol/state.json"

# Words that signal a final result. If any appears on the page, we ping.
TRIGGERS = [
    "Procedure completed",
    "Final act",
    "Act adopted",
    "rejected",
    "Rejection",
]

def fetch_page():
    headers = {"User-Agent": "Mozilla/5.0 (ping_web watcher)"}
    r = requests.get(URL, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text

def find_triggers(html):
    text = re.sub(r"<[^>]+>", " ", html)  # strip tags
    text = re.sub(r"\s+", " ", text)
    hits = [t for t in TRIGGERS if t.lower() in text.lower()]
    return hits

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"notified": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def notify(message):
    topic = os.environ["NTFY_TOPIC"]
    requests.post(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={
            "Title": "Chat Control 2.0 update",
            "Priority": "high",
            "Tags": "rotating_light",
        },
        timeout=30,
    )

def main():
    html = fetch_page()
    hits = find_triggers(html)
    state = load_state()
    new_hits = [h for h in hits if h not in state["notified"]]

    if new_hits:
        msg = "Legislative Observatory shows: " + ", ".join(new_hits) + "\n" + URL
        notify(msg)
        state["notified"].extend(new_hits)
        save_state(state)
        print("Notified:", new_hits)
    else:
        print("No new result. Current hits:", hits)

if __name__ == "__main__":
    main()
