"""
桶川市 ごみ収集日 Web API (v2)
東地区: 令和8年度 正確な収集日データ内蔵
西地区: 曜日ベース

uvicorn okegawa_gomi_api:app --reload
"""
from fastapi import FastAPI, Query, HTTPException
from datetime import date, datetime

app = FastAPI(
    title="桶川市ごみ収集日 API",
    description="桶川市の地区別ごみ収集日を返します。東地区は令和8年度の正確な日付データを保持しています。",
    version="2.0.0",
)

EAST_SCHEDULE = {
    "2026-04": {"month_ja":"4月","burnable":["2026-04-02","2026-04-06","2026-04-09","2026-04-13","2026-04-16","2026-04-20","2026-04-23","2026-04-27","2026-04-30"],"plastic":["2026-04-07","2026-04-14","2026-04-21","2026-04-28"],"metal_glass":["2026-04-10","2026-04-24"],"other":["2026-04-15"],"paper_containers":["2026-04-03","2026-04-17"],"recyclable":["2026-04-04","2026-04-18"]},
    "2026-05": {"month_ja":"5月","burnable":["2026-05-04","2026-05-07","2026-05-11","2026-05-14","2026-05-18","2026-05-21","2026-05-25","2026-05-28"],"plastic":["2026-05-05","2026-05-12","2026-05-19","2026-05-26"],"metal_glass":["2026-05-08","2026-05-22"],"other":["2026-05-20"],"paper_containers":["2026-05-01","2026-05-15"],"recyclable":["2026-05-02","2026-05-16"]},
    "2026-06": {"month_ja":"6月","burnable":["2026-06-01","2026-06-04","2026-06-08","2026-06-11","2026-06-15","2026-06-18","2026-06-22","2026-06-25","2026-06-29"],"plastic":["2026-06-02","2026-06-09","2026-06-16","2026-06-23","2026-06-30"],"metal_glass":["2026-06-12","2026-06-26"],"other":["2026-06-17"],"paper_containers":["2026-06-05","2026-06-19"],"recyclable":["2026-06-06","2026-06-20"]},
    "2026-07": {"month_ja":"7月","burnable":["2026-07-02","2026-07-06","2026-07-09","2026-07-13","2026-07-16","2026-07-20","2026-07-23","2026-07-27","2026-07-30"],"plastic":["2026-07-07","2026-07-14","2026-07-21","2026-07-28"],"metal_glass":["2026-07-10","2026-07-24"],"other":["2026-07-15"],"paper_containers":["2026-07-03","2026-07-17"],"recyclable":["2026-07-04","2026-07-18"]},
    "2026-08": {"month_ja":"8月","note":"お盆による休みはありません","burnable":["2026-08-03","2026-08-06","2026-08-10","2026-08-13","2026-08-17","2026-08-20","2026-08-24","2026-08-27","2026-08-31"],"plastic":["2026-08-04","2026-08-11","2026-08-18","2026-08-25"],"metal_glass":["2026-08-14","2026-08-28"],"other":["2026-08-19"],"paper_containers":["2026-08-07","2026-08-21"],"recyclable":["2026-08-01","2026-08-15"]},
    "2026-09": {"month_ja":"9月","burnable":["2026-09-03","2026-09-07","2026-09-10","2026-09-14","2026-09-17","2026-09-21","2026-09-24","2026-09-28"],"plastic":["2026-09-01","2026-09-08","2026-09-15","2026-09-22","2026-09-29"],"metal_glass":["2026-09-11","2026-09-25"],"other":["2026-09-16"],"paper_containers":["2026-09-04","2026-09-18"],"recyclable":["2026-09-05","2026-09-19"]},
    "2026-10": {"month_ja":"10月","burnable":["2026-10-01","2026-10-05","2026-10-08","2026-10-12","2026-10-15","2026-10-19","2026-10-22","2026-10-26","2026-10-29"],"plastic":["2026-10-06","2026-10-13","2026-10-20","2026-10-27"],"metal_glass":["2026-10-09","2026-10-23"],"other":["2026-10-21"],"paper_containers":["2026-10-02","2026-10-16"],"recyclable":["2026-10-03","2026-10-17"]},
    "2026-11": {"month_ja":"11月","burnable":["2026-11-02","2026-11-05","2026-11-09","2026-11-12","2026-11-16","2026-11-19","2026-11-23","2026-11-26","2026-11-30"],"plastic":["2026-11-03","2026-11-10","2026-11-17","2026-11-24"],"metal_glass":["2026-11-13","2026-11-27"],"other":["2026-11-18"],"paper_containers":["2026-11-06","2026-11-20"],"recyclable":["2026-11-07","2026-11-21"]},
    "2026-12": {"month_ja":"12月","note":"年末の収集日にご注意ください","burnable":["2026-12-03","2026-12-07","2026-12-10","2026-12-14","2026-12-17","2026-12-21","2026-12-24","2026-12-28","2026-12-31"],"plastic":["2026-12-01","2026-12-08","2026-12-15","2026-12-22","2026-12-29"],"metal_glass":["2026-12-11","2026-12-25"],"other":["2026-12-16"],"paper_containers":["2026-12-04","2026-12-18"],"recyclable":["2026-12-05","2026-12-19"]},
    "2027-01": {"month_ja":"1月","note":"資源（古着等）の収集日にご注意ください","burnable":["2027-01-04","2027-01-07","2027-01-11","2027-01-14","2027-01-18","2027-01-21","2027-01-25","2027-01-28"],"plastic":["2027-01-05","2027-01-12","2027-01-19","2027-01-26"],"metal_glass":["2027-01-15","2027-01-29"],"other":["2027-01-20"],"paper_containers":["2027-01-08","2027-01-22"],"recyclable":["2027-01-09","2027-01-23"]},
    "2027-02": {"month_ja":"2月","burnable":["2027-02-01","2027-02-04","2027-02-08","2027-02-11","2027-02-15","2027-02-18","2027-02-22","2027-02-25"],"plastic":["2027-02-02","2027-02-09","2027-02-16","2027-02-23"],"metal_glass":["2027-02-12","2027-02-26"],"other":["2027-02-17"],"paper_containers":["2027-02-05","2027-02-19"],"recyclable":["2027-02-06","2027-02-20"]},
    "2027-03": {"month_ja":"3月","burnable":["2027-03-01","2027-03-04","2027-03-08","2027-03-11","2027-03-15","2027-03-18","2027-03-22","2027-03-25","2027-03-29"],"plastic":["2027-03-02","2027-03-09","2027-03-16","2027-03-23","2027-03-30"],"metal_glass":["2027-03-12","2027-03-26"],"other":["2027-03-17"],"paper_containers":["2027-03-05","2027-03-19"],"recyclable":["2027-03-06","2027-03-20"]},
}

CATEGORY_NAMES = {
    "burnable":         "燃やせるごみ",
    "plastic":          "プラスチック",
    "metal_glass":      "金属・ガラス・乾電池",
    "other":            "その他ごみ（燃やせないごみ）",
    "paper_containers": "紙製の容器と包装紙",
    "recyclable":       "資源（古着・新聞紙・雑誌・段ボール・紙パック）",
}

WEST_WEEKDAY = [
    {"name": "燃やせるごみ",       "weekdays": [1, 4], "note": "毎週火・金曜日"},
    {"name": "プラスチック",       "weekdays": [3],    "note": "毎週木曜日"},
    {"name": "金属・ガラス・乾電池","weekdays": [0],    "note": "月2回（指定月曜日）"},
    {"name": "その他ごみ",         "weekdays": [2],    "note": "月1回（指定水曜日）"},
    {"name": "紙製の容器と包装紙", "weekdays": [0],    "note": "月2回（指定月曜日）"},
    {"name": "資源（古着等）",     "weekdays": [5],    "note": "月2回（指定土曜日）"},
]

WEEKDAY_JA = ["月","火","水","木","金","土","日"]
EAST_START = date(2026, 4, 1)
EAST_END   = date(2027, 3, 31)


def area_or_404(area):
    k = area.lower()
    if k not in ("west", "east"):
        raise HTTPException(404, detail=f"地区 '{area}' が見つかりません。'west' または 'east' を指定してください。")
    return k

def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(422, detail="日付は YYYY-MM-DD 形式で指定してください。")

def east_for_date(d):
    mk = d.strftime("%Y-%m")
    md = EAST_SCHEDULE.get(mk)
    if not md:
        return [], None
    ds = d.isoformat()
    cats = [{"category": k, "name": v} for k, v in CATEGORY_NAMES.items() if ds in md.get(k, [])]
    return cats, md.get("note")

def west_for_weekday(wd):
    return [{"category": c["name"], "name": c["name"], "note": c["note"]} for c in WEST_WEEKDAY if wd in c["weekdays"]]

def fmt_month(mk, md):
    out = {"month_ja": md["month_ja"]}
    if "note" in md:
        out["note"] = md["note"]
    for k, v in CATEGORY_NAMES.items():
        out[k] = {"name": v, "dates": md.get(k, [])}
    return out


@app.get("/")
def root():
    return {"name":"桶川市ごみ収集日 API","version":"2.0.0","docs":"/docs"}


@app.get("/schedule")
def get_schedule(
    area: str = Query(...),
    month: str = Query(None),
):
    k = area_or_404(area)
    if k == "west":
        return {
            "area":"west","display_name":"西地区（JR高崎線西側）","data_type":"weekday_based",
            "note":"西地区の日程表は未対応。正確な指定日は市公式サイトをご確認ください。",
            "categories":[{"name":c["name"],"weekdays":[WEEKDAY_JA[w]+"曜日" for w in c["weekdays"]],"note":c["note"]} for c in WEST_WEEKDAY],
            "source":"https://www.city.okegawa.lg.jp/kurashi/gomi_kankyo/gomi_recycle/shushubi/2360.html",
        }
    if month:
        md = EAST_SCHEDULE.get(month)
        if not md:
            raise HTTPException(404, detail=f"月 '{month}' のデータがありません。対応期間: 2026-04 〜 2027-03")
        sched = {month: fmt_month(month, md)}
    else:
        sched = {m: fmt_month(m, d) for m, d in EAST_SCHEDULE.items()}
    return {"area":"east","display_name":"東地区（JR高崎線東側）","data_type":"exact_dates","period":"2026-04-01 〜 2027-03-31","source":"桶川市配布 令和8年度ごみ収集日程表（東側地区版）","schedule":sched}


@app.get("/today")
def get_today(area: str = Query(...)):
    k = area_or_404(area)
    today = date.today()
    wd = today.weekday()
    if k == "east":
        in_range = EAST_START <= today <= EAST_END
        if in_range:
            cats, note = east_for_date(today)
            return {"area":"east","display_name":"東地区（JR高崎線東側）","date":today.isoformat(),"weekday":WEEKDAY_JA[wd]+"曜日","data_type":"exact_dates","month_note":note,"categories":cats,"message":f"{len(cats)} 種類のごみを収集します。" if cats else "本日はごみ収集はありません。"}
        return {"area":"east","date":today.isoformat(),"data_type":"out_of_range","categories":[],"message":"データ期間外のため市公式サイトをご確認ください。"}
    cats = west_for_weekday(wd)
    return {"area":"west","display_name":"西地区（JR高崎線西側）","date":today.isoformat(),"weekday":WEEKDAY_JA[wd]+"曜日","data_type":"weekday_based","categories":cats,"message":f"{len(cats)} 種類のごみを収集します（曜日ベース）。" if cats else "本日はごみ収集はありません（曜日ベース）。"}


@app.get("/query")
def get_by_date(
    area: str = Query(...),
    date_str: str = Query(..., alias="date"),
):
    k = area_or_404(area)
    t = parse_date(date_str)
    wd = t.weekday()
    if k == "east":
        in_range = EAST_START <= t <= EAST_END
        if in_range:
            cats, note = east_for_date(t)
            return {"area":"east","display_name":"東地区（JR高崎線東側）","date":t.isoformat(),"weekday":WEEKDAY_JA[wd]+"曜日","data_type":"exact_dates","month_note":note,"categories":cats,"message":f"{len(cats)} 種類のごみを収集します。" if cats else "この日はごみ収集はありません。"}
        return {"area":"east","date":t.isoformat(),"data_type":"out_of_range","categories":[],"message":"データ期間外（2026-04〜2027-03）です。市公式サイトをご確認ください。"}
    cats = west_for_weekday(wd)
    return {"area":"west","display_name":"西地区（JR高崎線西側）","date":t.isoformat(),"weekday":WEEKDAY_JA[wd]+"曜日","data_type":"weekday_based","categories":cats,"message":f"{len(cats)} 種類のごみを収集します（曜日ベース）。" if cats else "この日はごみ収集はありません（曜日ベース）。"}
