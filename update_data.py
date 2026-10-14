#!/usr/bin/env python3
"""KBO 공식 사이트에서 순위·선수기록·경기일정/결과를 읽어 data.json 을 갱신합니다.
- 일부 항목만 실패해도 나머지는 갱신하고, 실패한 항목은 기존 값을 유지합니다.
- 개인 학습/비영리 용도로 쓰고, 호출 간격을 두어 서버에 부담을 주지 않습니다.
"""
import json, re, sys, time, datetime as dt
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE = "https://www.koreabaseball.com"
HEAD = {"User-Agent": "Mozilla/5.0 (kbo-hub personal fan site)",
        "Referer": BASE + "/Schedule/Schedule.aspx"}
OUT = Path(__file__).resolve().parent / "data.json"
KST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime.now(KST)

def get(url, **kw):
    r = requests.get(url, headers=HEAD, timeout=30, **kw); r.raise_for_status()
    time.sleep(1); return r.text

def post(url, data):
    r = requests.post(url, headers=HEAD, data=data, timeout=30); r.raise_for_status()
    time.sleep(1); return r.json()

def txt(el): return el.get_text(" ", strip=True)

# ---------- 1) 팀 순위 + 팀간 승패표 ----------
def standings():
    soup = BeautifulSoup(get(BASE + "/Record/TeamRank/TeamRankDaily.aspx"), "html.parser")
    tables = soup.select("table.tData")
    rows = []
    for tr in tables[0].select("tbody tr"):
        c = [txt(td) for td in tr.find_all("td")]
        if len(c) < 12: continue
        g = c[7]
        rows.append([c[1], int(c[2]), int(c[3]), int(c[4]), int(c[5]), c[6],
                     "-" if g in ("0", "0.0") else g, c[8], c[9], c[10], c[11]])
    if len(rows) != 10: raise ValueError(f"순위 행 {len(rows)}개")
    teams = [r[0] for r in rows]
    h2h = {}
    for tr in tables[1].select("tbody tr"):
        c = [txt(td) for td in tr.find_all("td")]
        if len(c) >= 11 and c[0] in teams:
            h2h[c[0]] = ["-" if x == "■" else x for x in c[1:11]]
    if len(h2h) != 10: raise ValueError("팀간 승패표 파싱 실패")
    return rows, h2h

# ---------- 2) 선수 순위 (KBO 공식 TOP5) ----------
HIT = {"타율": "AVG", "홈런": "HR", "타점": "RBI", "안타": "H", "득점": "R",
       "도루": "SB", "출루율": "OBP", "장타율": "SLG", "OPS": "OPS"}
PIT = {"평균자책점": ("평균자책점", "ERA"), "승리": ("다승", "W"), "세이브": ("세이브", "SV"),
       "승률": ("승률", "WPCT(10승↑)"), "홀드": ("홀드", "HLD"), "탈삼진": ("탈삼진", "K")}

def leaders():
    soup = BeautifulSoup(get(BASE + "/Record/Ranking/Top5.aspx"), "html.parser")
    found = {}; side = "타자"
    for box in soup.select("div.record"):
        t = box.select_one(".title_bar .title")
        if not t: continue
        title = re.sub(r"\s*TOP5.*", "", txt(t)).strip()
        if title == "평균자책점": side = "투수"
        elif title == "타율": side = "타자"
        key = title.split("(")[0].strip()
        items = []
        for li in box.select("ol.rankList li"):
            n, tm, v = li.select_one(".name"), li.select_one(".team"), li.select_one(".rr")
            if n and tm and v: items.append([txt(n), txt(tm), txt(v)])
        if side == "타자" and key in HIT and key not in found:
            found[key] = {"u": HIT[key], "g": "타자", "v": items}
        if side == "투수" and key in PIT and PIT[key][0] not in found:
            nm, u = PIT[key]; found[nm] = {"u": u, "g": "투수", "v": items}
    order = list(HIT) + [v[0] for v in PIT.values()]
    out = {k: found[k] for k in order if k in found and found[k]["v"]}
    if len(out) < 8: raise ValueError(f"선수 부문 {len(out)}개만 파싱")
    return out

# ---------- 3) 경기 일정/결과 ----------
def schedule():
    year = NOW.year
    games = []
    for m in range(max(3, NOW.month - 1), min(11, NOW.month + 1) + 1):
        for series in ("0,9,6", "3,4,5,7"):          # 정규시즌 / 포스트시즌
            d = post(BASE + "/ws/Schedule.asmx/GetScheduleList",
                     {"leId": 1, "srIdList": series, "seasonId": year,
                      "gameMonth": f"{m:02d}", "teamId": ""})
            day = ""
            for r in d.get("rows", []):
                cells = r["row"]
                if cells and cells[0].get("Class") == "day":
                    day = cells[0]["Text"]; cells = cells[1:]
                by = {}
                for c in cells:
                    if c.get("Class"): by[c["Class"]] = c["Text"]
                if "play" not in by: continue
                sp = BeautifulSoup(by["play"], "html.parser")
                top = sp.find_all("span", recursive=False)
                if len(top) < 2: continue
                away, home = txt(top[0]), txt(top[-1])
                nums = [txt(s) for s in sp.select("em span") if txt(s).isdigit()]
                tail = [BeautifulSoup(c["Text"], "html.parser").get_text(" ", strip=True) for c in cells[-2:]]
                mm = re.match(r"(\d+)\.(\d+)", day)
                games.append({"month": int(mm.group(1)), "d": int(mm.group(2)),
                              "day": day, "time": re.sub("<[^>]+>", "", by.get("time", "")),
                              "away": away, "home": home,
                              "as": int(nums[0]) if len(nums) == 2 else None,
                              "hs": int(nums[1]) if len(nums) == 2 else None,
                              "place": tail[0], "note": tail[1] if tail[1] != "-" else "",
                              "post": series.startswith("3")})
    if not games: raise ValueError("경기 없음")
    games.sort(key=lambda g: (g["month"], g["d"], g["time"]))
    done = [g for g in games if g["as"] is not None]
    today = (NOW.month, NOW.day)
    todo = [g for g in games if g["as"] is None and "취소" not in g["note"] and (g["month"], g["d"]) >= today]
    results = [{"date": f'{g["month"]:02d}/{g["d"]:02d}', "away": g["away"], "as": g["as"],
                "home": g["home"], "hs": g["hs"], "place": g["place"], "post": g["post"]}
               for g in reversed(done)][:60]
    sched = [{"date": g["day"].replace(".", "/", 1), "time": g["time"],
              "stage": "포스트시즌" if g["post"] else "정규시즌",
              "away": g["away"], "home": g["home"], "place": g["place"], "note": g["note"]}
             for g in todo][:30]
    return sched, results

def main():
    old = json.loads(OUT.read_text(encoding="utf8")) if OUT.exists() else {}
    new = dict(old); ok = 0
    for name, fn in (("순위", standings), ("선수순위", leaders), ("일정/결과", schedule)):
        try:
            v = fn(); ok += 1
            if name == "순위": new["standings"], new["h2h"] = v
            elif name == "선수순위": new["leaders"] = v
            else: new["schedule"], new["results"] = v
            print("OK  ", name)
        except Exception as e:
            print("FAIL", name, "→ 기존 값 유지:", repr(e), file=sys.stderr)
    if ok == 0: sys.exit("모든 항목 실패 — data.json 변경 안 함")
    new["updated"] = NOW.strftime("%Y-%m-%d %H:%M KST")
    OUT.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf8")
    print("saved", OUT, new["updated"])

if __name__ == "__main__":
    main()
