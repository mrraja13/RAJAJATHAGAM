import os, json, base64, urllib.request

REPO = "mrraja13/RAJAJATHAGAM"
PATH = "backup/jathagam_backup.json"
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_charts")

def token():
    with open(os.path.expanduser("~/.gh_token")) as f:
        return f.read().strip()

def api(method, url, payload=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", "token " + token())
    req.add_header("Accept", "application/vnd.github+json")
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, body) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

def run():
    charts = {}
    if os.path.isdir(DIR):
        for f in os.listdir(DIR):
            if f.endswith(".json"):
                with open(os.path.join(DIR, f), encoding="utf-8") as fh:
                    try:
                        charts[f[:-5]] = json.load(fh)
                    except Exception:
                        pass
    content = json.dumps({"version": 1, "charts": charts}, ensure_ascii=False, indent=1)
    b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    url = "https://api.github.com/repos/%s/contents/%s" % (REPO, PATH)
    cur = api("GET", url)
    payload = {"message": "jathagam backup", "content": b64}
    if cur and cur.get("sha"):
        payload["sha"] = cur["sha"]
    api("PUT", url, payload)
    return len(charts)

def restore():
    """GitHub-இலிருந்து ஜாதகங்களை மீட்டெடு — உள்ளூரில் இல்லாதவை மட்டும்"""
    url = "https://api.github.com/repos/%s/contents/%s" % (REPO, PATH)
    cur = api("GET", url)
    if not cur or not cur.get("content"):
        return 0
    raw = base64.b64decode(cur["content"]).decode("utf-8")
    charts = json.loads(raw).get("charts", {})
    os.makedirs(DIR, exist_ok=True)
    n = 0
    for name, data in charts.items():
        safe = "".join(ch for ch in str(name) if ch not in '/\\:*?"<>|').strip()
        if not safe:
            continue
        p = os.path.join(DIR, safe + ".json")
        if os.path.exists(p):
            continue
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)
        n += 1
    return n

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        print("restored:", restore())
    else:
        print("backed up:", run())
