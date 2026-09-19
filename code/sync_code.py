import os, json, base64, urllib.request, sys

REPO = "mrraja13/RAJAJATHAGAM"
BASE = os.path.dirname(os.path.abspath(__file__))
FILES = ["app.py", "astro_engine.py", "templates/dashboard.html", "backup_to_github.py", "sync_code.py"]

def token():
    with open(os.path.expanduser("~/.gh_token")) as f:
        return f.read().strip()

def api(method, url, payload=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", "token " + token())
    req.add_header("Accept", "application/vnd.github+json")
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, body) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

def push():
    n = 0
    for rel in FILES:
        p = os.path.join(BASE, rel)
        if not os.path.exists(p):
            continue
        with open(p, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        url = "https://api.github.com/repos/%s/contents/code/%s" % (REPO, rel)
        cur = api("GET", url)
        payload = {"message": "sync " + rel, "content": b64}
        if cur and cur.get("sha"):
            payload["sha"] = cur["sha"]
        api("PUT", url, payload)
        n += 1
        print("  pushed:", rel)
    return n

def pull():
    n = 0
    for rel in FILES:
        url = "https://api.github.com/repos/%s/contents/code/%s" % (REPO, rel)
        cur = api("GET", url)
        if not cur or not cur.get("content"):
            print("  missing on github:", rel)
            continue
        data = base64.b64decode(cur["content"])
        p = os.path.join(BASE, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)
        n += 1
        print("  pulled:", rel)
    return n

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "push"
    if mode == "pull":
        print("pulled files:", pull())
    else:
        print("pushed files:", push())
