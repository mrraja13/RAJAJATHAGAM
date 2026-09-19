# -*- coding: utf-8 -*-
import os, json, sys

BASE = os.path.dirname(os.path.abspath(__file__))
RULES_FILE = os.path.join(BASE, "palan_rules.json")

GRAHA = {"sun":"சூரியன்","moon":"சந்திரன்","mars":"செவ்வாய்","mercury":"புதன்",
         "jupiter":"குரு","venus":"சுக்கிரன்","saturn":"சனி","rahu":"ராகு",
         "ketu":"கேது","lagna":"லக்னம்","gulika":"குளிகன்"}

def load():
    if not os.path.exists(RULES_FILE):
        return []
    with open(RULES_FILE, encoding="utf-8") as f:
        return json.load(f)

def save(rules):
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=1)

def add(graha, cond, text, varga="D1"):
    rules = load()
    rules.append({"id": len(rules)+1, "varga": varga, "graha": graha.lower(),
                  "cond": cond, "text": text})
    save(rules)
    return len(rules)

def show():
    rules = load()
    if not rules:
        print("விதிகள் இல்லை")
        return
    for r in rules:
        print("%-3s %-5s %-10s %-24s %s" % (r["id"], r["varga"],
              GRAHA.get(r["graha"], r["graha"]), r["cond"], r["text"][:45]))

def delete(rid):
    rules = [r for r in load() if r["id"] != int(rid)]
    for i, r in enumerate(rules):
        r["id"] = i + 1
    save(rules)
    return len(rules)

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "list":
        show()
    elif a[0] == "add" and len(a) >= 4:
        varga = a[4] if len(a) > 4 else "D1"
        print("சேர்க்கப்பட்டது. மொத்தம்:", add(a[1], a[2], a[3], varga))
    elif a[0] == "del" and len(a) >= 2:
        print("மீதம்:", delete(a[1]))
    else:
        print("பயன்பாடு:")
        print("  python3 rules.py list")
        print('  python3 rules.py add <graha> <cond> "<palan>" [varga]')
        print("  python3 rules.py del <id>")
        print("")
        print("நிபந்தனைகள்: bhava=10 | bhava=1,4,7,10 | sarva>30 | bhinna>=5 | owns=10 | status=uccham")
        print("")
        print('எ.கா: python3 rules.py add sun bhava=10 "அரசு வேலை"')
