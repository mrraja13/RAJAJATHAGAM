from flask import Flask, render_template, request, make_response, send_from_directory
import json as _json

def jsonify(data):
    resp = make_response(_json.dumps(data, ensure_ascii=False))
    resp.content_type = 'application/json; charset=utf-8'
    return resp


app = Flask(__name__)
app.json.sort_keys = False
app.json.ensure_ascii = False
app.config['JSON_ENSURE_ASCII'] = False

from datetime import datetime, timedelta
import os, json
import astro_engine as ae


LAT = 8.3333
LON = 77.8500
DEFAULT_DOB = "1979-10-05"
DEFAULT_TOB = "10:10:28"

SAVED_CHARTS_DIR = os.path.expanduser("~/raja_jathagam_test/saved_charts")
os.makedirs(SAVED_CHARTS_DIR, exist_ok=True)

def now_ist():
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    return (utc_now + ist_offset).replace(tzinfo=None)

DASHA_LORDS = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
DASHA_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,"Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}
TOTAL_YEARS = 120

def get_moon_sidereal_longitude(year,month,day,hour_ist,tz_offset=5.5):
    longs,_ = ae.get_all_sidereal_longitudes(year,month,day,hour_ist,LAT,LON,tz_offset)
    return longs["Moon"]

def add_years(dt,years):
    try: return dt.replace(year=dt.year+int(years))
    except: return dt+timedelta(days=years*365.25)

def sub_periods(lord,start,years,depth=0,min_date=None):
    periods=[]
    cur=start
    start_idx=DASHA_LORDS.index(lord)
    for i in range(9):
        sub=DASHA_LORDS[(start_idx+i)%9]
        sub_yrs=years*DASHA_YEARS[sub]/TOTAL_YEARS
        end=cur+timedelta(days=sub_yrs*365.25)
        if min_date is None or end>=min_date:
            periods.append({"lord":sub,"start":cur.strftime("%d-%m-%Y %H:%M"),"end":end.strftime("%d-%m-%Y %H:%M"),"years":round(sub_yrs,4),"children":[]})
        cur=end
    return periods

def _compute_children(lord,start,years,min_date=None):
    children=sub_periods(lord,start,years,min_date=min_date)
    return children

def _find_current_position(tree,target_date):
    def find_in(nodes,target):
        for node in nodes:
            try:
                s=datetime.strptime(node["start"],"%d-%m-%Y %H:%M")
                e=datetime.strptime(node["end"],"%d-%m-%Y %H:%M")
            except: continue
            if s<=target<e: return node
        return None
    return find_in(tree,target_date)
def build_dasa_120(birth_date,moon_sid):
    nak_span=360.0/27.0
    nak_idx=int(moon_sid//nak_span)
    balance_fraction=1.0-((moon_sid%nak_span)/nak_span)
    lord=DASHA_LORDS[nak_idx%9]
    balance_years=DASHA_YEARS[lord]*balance_fraction
    mahadasas=[]
    cur=birth_date
    start_idx=DASHA_LORDS.index(lord)
    first_end=cur+timedelta(days=balance_years*365.25)
    mahadasas.append({"lord":lord,"start":cur.strftime("%d-%m-%Y %H:%M"),"end":first_end.strftime("%d-%m-%Y %H:%M"),"years":round(balance_years,4),"children":[]})
    cur=first_end
    for i in range(1,9):
        l=DASHA_LORDS[(start_idx+i)%9]
        yrs=DASHA_YEARS[l]
        end=cur+timedelta(days=yrs*365.25)
        mahadasas.append({"lord":l,"start":cur.strftime("%d-%m-%Y %H:%M"),"end":end.strftime("%d-%m-%Y %H:%M"),"years":round(yrs,4),"children":[]})
        cur=end
    return mahadasas

def _parse_tob(tob):
    parts=tob.strip().split(":")
    hh=int(parts[0]) if len(parts)>0 else 10
    mm=int(parts[1]) if len(parts)>1 else 10
    ss=int(parts[2]) if len(parts)>2 else 0
    return hh,mm,ss

def _extract_birth_from_request(data):
    dob=data.get("dob","1979-10-05")
    tob=data.get("tob","10:10:28")
    y,mo,d=[int(x) for x in dob.split("-")]
    hh,mm,ss=_parse_tob(tob)
    lat=float(data.get("lat",LAT))
    lon=float(data.get("lon",LON))
    return y,mo,d,hh,mm,ss,lat,lon

def _build_spudam_and_vargas(year,month,day,hh,mm,ss,lat,lon):
    hour_ist=hh+mm/60.0+ss/3600.0
    longs,jd_ut=ae.get_all_sidereal_longitudes(year,month,day,hour_ist,lat,lon)
    weekday_en=datetime(year,month,day).strftime("%A")
    sunrise_jd,sunset_jd=ae.get_sunrise_sunset(year,month,day,lat,lon)
    if sunrise_jd is not None and sunset_jd is not None:
        is_day=(jd_ut>=sunrise_jd and jd_ut<sunset_jd)
    else: is_day=True
    gulika_lon,_=ae.get_gulika_longitude(longs["Sun"],weekday_en,is_day)
    longs["Gulika"]=gulika_lon
    spudam_list=[]
    graha_order=["Lagna","Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu","Gulika"]
    for g in graha_order:
        if g not in longs or longs[g] is None: continue
        lon_val=longs[g]
        sign_idx,deg=ae.lon_to_sign_deg(lon_val)
        nak,pada=ae.lon_to_nak_pada(lon_val)
        status=ae.graha_status(g,sign_idx)
        row={"body":ae.GRAHA_TA[g],"rasi":ae.SIGNS_TA[sign_idx],"dms":ae.deg_to_dms(deg),"nak_pada":f"{nak} - {pada}","status":status,"special2":"-","karaka":"-","_sign_idx":sign_idx,"_deg":deg}
        spudam_list.append(row)
    vargas=ae.compute_all_vargas(longs)
    for row in spudam_list:
        g_en=[k for k,v in ae.GRAHA_TA.items() if v==row["body"]][0]
        d9_idx=vargas["D9"].get(g_en)
        row["d9_sign"]=ae.SIGNS_TA[d9_idx] if d9_idx is not None else "-"
        row.pop("_sign_idx",None)
        row.pop("_deg",None)
    astangam=ae.compute_astangam(longs)
    kiraganam=ae.compute_kiraganam(longs)
    yuddha=ae.compute_graha_yuddha(longs)
    for row in spudam_list:
        g_en=[k for k,v in ae.GRAHA_TA.items() if v==row["body"]][0]
        lon_val=longs.get(g_en)
        badges=[]
        a_tier=astangam.get(g_en)
        if a_tier=='light': badges.append('<span style="color:#ffb74d;font-weight:bold;">அஸ்தங்கம்</span>')
        elif a_tier=='dark': badges.append('<span style="color:#e65100;font-weight:bold;">அஸ்தங்கம்</span>')
        k_tier=kiraganam.get(g_en)
        if k_tier=='light': badges.append('<span style="color:#bdbdbd;">கிரகணம்</span>')
        elif k_tier=='dark': badges.append('<span style="color:#616161;">கிரகணம்</span>')
        if yuddha.get(g_en): badges.append('<span style="color:#c62828;font-weight:bold;">கிரகயுத்தம்</span>')
        if lon_val is not None:
            si2,deg2=ae.lon_to_sign_deg(lon_val)
        if ae.is_pushkara_navamsa(si2,deg2): badges.append('<span style="color:#2e7d32;">புஷ்கரம்</span>')
        row["special2"]=", ".join(badges) if badges else "-"
    house_highlights_raw=ae.compute_own_house_highlights(longs)
    house_highlights={str(k):v for k,v in house_highlights_raw.items()}
    karakas=ae.compute_karakas(longs)
    for row in spudam_list:
        row["karaka"]=next((k for k,v in karakas.items() if v==row["body"]),"-")
    varga_charts=[]
    for vkey in ["D1","D2","D3","D4","D5","D6","D7","D8","D9","D10","D11","D12","D15","D16","D18","D20","D22","D24","D27","D30","D36","D40","D45","D60","D144"]:
        grid=ae.build_grid_from_signs(vargas[vkey])
        name_ta=ae.VARGA_NAMES_TA.get(vkey,vkey)
        varga_charts.append({"name":name_ta,"grid":grid})
    sign_idx_map={}
    for g,lon_val in longs.items():
        if lon_val is None: continue
        si,_=ae.lon_to_sign_deg(lon_val)
        sign_idx_map[g]=si
    bhinnas,sarva=ae.compute_ashtakavarga(sign_idx_map)
    prasthara={}
    graha_names={"Sun":"சூரியன்","Moon":"சந்திரன்","Mars":"செவ்வாய்","Mercury":"புதன்","Jupiter":"குரு","Venus":"சுக்கிரன்","Saturn":"சனி"}
    for g_en,pts in bhinnas.items():
        ta_name=graha_names.get(g_en,g_en)
        prasthara[ta_name]={str(i+1):pts[i] for i in range(12)}
    ashtakavarga={"sarva":sarva,"prasthara":prasthara}
    horas=ae.compute_hora_list(year,month,day,lat,lon)
    today_ist=now_ist()
    todays_horas=ae.compute_hora_list(today_ist.year,today_ist.month,today_ist.day,lat,lon)
    return spudam_list,varga_charts,ashtakavarga,horas,todays_horas,house_highlights


@app.route('/dash')
def dash_direct():
    with open('static/index.html', encoding='utf-8') as f:
        content = f.read()
    return content

@app.route("/",methods=["GET","POST"])
def home():
    from flask import Response
    with open("templates/dashboard.html",encoding="utf-8") as f:
        html=f.read()
    html=html.replace("{%","<!--").replace("%}","-->")
    return Response(html,mimetype="text/html")

@app.route("/upload_jathagam_file",methods=["POST"])
def upload_jathagam_file():
    return jsonify({"status":"error","message":"Not implemented"})

def _safe_longs(y,mo,d,hh,mm,ss,lat,lon):
    try:
        _hr = hh+mm/60.0+ss/3600.0
        _l,_jd = ae.get_all_sidereal_longitudes(y,mo,d,_hr,lat,lon)
        try:
            _wd = datetime(y,mo,d).strftime("%A")
            _sr,_ss = ae.get_sunrise_sunset(y,mo,d,lat,lon)
            _isday = (_jd >= _sr and _jd < _ss) if (_sr is not None and _ss is not None) else True
            _g,_ = ae.get_gulika_longitude(_l["Sun"], _wd, _isday)
            _l["Gulika"] = _g
        except Exception:
            pass
        return {k: v for k, v in _l.items() if v is not None}
    except Exception:
        return {}

def _safe_grp(y,mo,d,hh,mm,ss,lat,lon,which):
    try:
        _l,_ = ae.get_all_sidereal_longitudes(y,mo,d,hh+mm/60.0+ss/3600.0,lat,lon)
        return ae.compute_d3_all(_l) if which=="d3" else ae.compute_d16_all(_l)
    except Exception:
        return []

def _safe_d2(y,mo,d,hh,mm,ss,lat,lon):
    try:
        _l,_ = ae.get_all_sidereal_longitudes(y,mo,d,hh+mm/60.0+ss/3600.0,lat,lon)
        return ae.compute_d2_all(_l)
    except Exception:
        return []

def _safe_diffs(y,mo,d,hh,mm,ss,lat,lon):
    try:
        _l = _safe_longs(y,mo,d,hh,mm,ss,lat,lon)
        return ae.verify_vargas(_l)
    except Exception:
        return []

@app.route("/get_varga_predictions",methods=["GET","POST"])
def get_varga_predictions():
    data=request.get_json(silent=True) or request.form.to_dict() or {}
    year,month,day,hh,mm,ss,lat,lon=_extract_birth_from_request(data)
    try:
        spudam_list,varga_charts,ashtakavarga,horas,todays_horas,house_highlights=_build_spudam_and_vargas(year,month,day,hh,mm,ss,lat,lon)
    except Exception as e:
        return jsonify({"status":"error","message":str(e)})
    moon_sid=get_moon_sidereal_longitude(year,month,day,hh+mm/60.0+ss/3600.0)
    birth_date=datetime(year,month,day,hh,mm,ss)
    mahadasas=build_dasa_120(birth_date,moon_sid)
    dasha_info={"birth_date":birth_date.strftime("%d-%m-%Y"),"birth_time":f"{hh:02d}:{mm:02d}:{ss:02d}","mahadasas":mahadasas}
    return jsonify({"status":"success","varga_charts":varga_charts,"spudam_list":spudam_list,"ashtakavarga":ashtakavarga,"dasha_info":dasha_info,"house_highlights":house_highlights,"longitudes":_safe_longs(year,month,day,hh,mm,ss,lat,lon),"unverified_vargas":sorted(set(ae.VARGA_FUNCS)-ae.VERIFIED_VARGAS),"varga_diffs":_safe_diffs(year,month,day,hh,mm,ss,lat,lon),"d2_methods":_safe_d2(year,month,day,hh,mm,ss,lat,lon),"d3_methods":_safe_grp(year,month,day,hh,mm,ss,lat,lon,"d3"),"d16_methods":_safe_grp(year,month,day,hh,mm,ss,lat,lon,"d16")})


def _graha_context(birth_args):
    """ஒவ்வொரு கிரகத்துக்கும்: ராசி, பாவம், ஆட்சி பாவங்கள், சர்வ/பின்ன புள்ளிகள்"""
    year, month, day, hh, mm, ss, lat, lon = birth_args
    hour_ist = hh + mm/60.0 + ss/3600.0
    longs, jd_ut = ae.get_all_sidereal_longitudes(year, month, day, hour_ist, lat, lon)
    lagna_sign = int(longs["Lagna"] // 30)
    signs = {g: int(v // 30) for g, v in longs.items() if v is not None}
    bhinnas, sarva = ae.compute_ashtakavarga(signs)
    OWN = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],
           "Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10]}
    ctx = {}
    for g_en in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]:
        if g_en not in signs:
            continue
        sg = signs[g_en]
        bhava = ((sg - lagna_sign) % 12) + 1
        own_bhavas = sorted(((s - lagna_sign) % 12) + 1 for s in OWN.get(g_en, []))
        ctx[g_en] = {
            "rasi": ae.SIGNS_TA[sg],
            "bhava": bhava,
            "owns": own_bhavas,
            "sarva": sarva[sg] if sarva else 0,
            "bhinna": bhinnas.get(g_en, [0]*12)[sg] if g_en in bhinnas else None,
        }
    return ctx

def _attach_ctx(nodes, ctx):
    for n in nodes:
        gc = ctx.get(n.get("lord"))
        n["lord_ta"] = ae.GRAHA_TA.get(n.get("lord"), n.get("lord"))
        if gc:
            n["rasi"] = gc["rasi"]
            n["bhava"] = gc["bhava"]
            n["owns"] = gc["owns"]
            n["sarva"] = gc["sarva"]
            n["bhinna"] = gc["bhinna"]
    return nodes

@app.route("/get_dasha_120",methods=["POST"])
def get_dasha_120():
    data=request.get_json(silent=True) or {}
    year,month,day,hh,mm,ss,lat,lon=_extract_birth_from_request(data)
    moon_sid=get_moon_sidereal_longitude(year,month,day,hh+mm/60.0+ss/3600.0)
    birth_date=datetime(year,month,day,hh,mm,ss)
    mahadasas=build_dasa_120(birth_date,moon_sid)
    try:
        _ctx=_graha_context((year,month,day,hh,mm,ss,LAT,LON))
        _attach_ctx(mahadasas,_ctx)
    except Exception as _e:
        pass
    return jsonify({"status":"success","mahadasas":mahadasas})

@app.route("/get_dasha_children",methods=["POST"])
def get_dasha_children():
    data=request.get_json(silent=True) or {}
    lord=data.get("lord")
    start_str=data.get("start")
    years=float(data.get("years",0))
    level=int(data.get("level",1))
    try:
        start=datetime.strptime(start_str,"%d-%m-%Y %H:%M")
    except: return jsonify({"status":"error","message":"bad date"})
    children=_compute_children(lord,start,years)
    try:
        _ctx=_graha_context((1979,10,5,10,10,28,LAT,LON))
        _attach_ctx(children,_ctx)
    except Exception:
        pass
    return jsonify({"status":"success","children":children})


NAK_TA = ["அசுவினி","பரணி","கார்த்திகை","ரோகிணி","மிருகசீரிடம்","திருவாதிரை","புனர்பூசம்","பூசம்","ஆயில்யம்","மகம்","பூரம்","உத்திரம்","அஸ்தம்","சித்திரை","சுவாதி","விசாகம்","அனுஷம்","கேட்டை","மூலம்","பூராடம்","உத்திராடம்","திருவோணம்","அவிட்டம்","சதயம்","பூரட்டாதி","உத்திரட்டாதி","ரேவதி"]
NAK_LORD = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"] * 3
TITHI_TA = ["பிரதமை","துவிதியை","திருதியை","சதுர்த்தி","பஞ்சமி","சஷ்டி","சப்தமி","அஷ்டமி","நவமி","தசமி","ஏகாதசி","துவாதசி","திரயோதசி","சதுர்த்தசி","பௌர்ணமி"]
YOGA_TA = ["விஷ்கம்பம்","ப்ரீதி","ஆயுஷ்மான்","சௌபாக்யம்","சோபனம்","அதிகண்டம்","சுகர்மம்","திருதி","சூலம்","கண்டம்","விருத்தி","துருவம்","வியாகாதம்","ஹர்ஷணம்","வஜ்ரம்","சித்தி","வ்யதீபாதம்","வரியான்","பரிகம்","சிவம்","சித்தம்","சாத்யம்","சுபம்","சுப்ரம்","ப்ராஹ்மம்","ஐந்திரம்","வைத்ருதி"]
KARANA_TA = ["பவம்","பாலவம்","கௌலவம்","தைதுலம்","கரஜை","வணிஜை","விஷ்டி (பத்தரை)"]
WEEKDAY_TA = {"Monday":"திங்கள்","Tuesday":"செவ்வாய்","Wednesday":"புதன்","Thursday":"வியாழன்","Friday":"வெள்ளி","Saturday":"சனி","Sunday":"ஞாயிறு"}


YONI_TA = ["குதிரை","யானை","ஆடு","பாம்பு","பாம்பு","நாய்","பூனை","ஆடு","பூனை","எலி","எலி","பசு","எருமை","புலி","எருமை","புலி","மான்","மான்","நாய்","குரங்கு","குரங்கு","கீரி","சிங்கம்","குதிரை","சிங்கம்","பசு","யானை"]
HORA_ORDER = ["Sun","Venus","Mercury","Moon","Saturn","Jupiter","Mars"]
DAY_LORD = {"Sunday":"Sun","Monday":"Moon","Tuesday":"Mars","Wednesday":"Mercury","Thursday":"Jupiter","Friday":"Venus","Saturday":"Saturn"}
PAKSHI_TA = ["வல்லூறு","ஆந்தை","காகம்","கோழி","மயில்"]

def _compute_hora(y, mo, d, hour_ist, lat, lon, wd_en):
    try:
        sr_jd, ss_jd = ae.get_sunrise_sunset(y, mo, d, lat, lon)
        if sr_jd is None:
            return None
        import swisseph as swe
        sr_ut = swe.revjul(sr_jd)
        sr_hour_ut = sr_ut[3]
        sr_ist = sr_hour_ut + 5.5
        if sr_ist >= 24: sr_ist -= 24
        elapsed = hour_ist - sr_ist
        if elapsed < 0: elapsed += 24
        hora_idx = int(elapsed)
        start = HORA_ORDER.index(DAY_LORD.get(wd_en, "Sun"))
        lord = HORA_ORDER[(start + hora_idx) % 7]
        return ae.GRAHA_TA.get(lord, lord)
    except Exception:
        return None

def _compute_pakshi(nak_idx, paksha_is_sukla):
    grp = nak_idx // 6 if nak_idx < 25 else 4
    if paksha_is_sukla:
        return PAKSHI_TA[grp % 5]
    return PAKSHI_TA[(4 - (grp % 5)) % 5]

VRIKSHA_TA = ["விஷமுட்டி","நெல்லி","அத்தி","நாவல்","கருங்காலி","முருக்கு","மூங்கில்","அரசு","புன்னை","ஆல்","பலா","அரசு","வன்னி","வில்வம்","மருது","விளா","இலந்தை","புங்கை","வாகை","பலா","பலா","எருக்கு","வன்னி","கருங்காலி","மா","வேம்பு","இலுப்பை"]
GANA_TA = ["தேவ","மனுஷ","ராட்சத","மனுஷ","தேவ","மனுஷ","தேவ","தேவ","ராட்சத","ராட்சத","மனுஷ","மனுஷ","தேவ","ராட்சத","தேவ","ராட்சத","தேவ","ராட்சத","ராட்சத","மனுஷ","மனுஷ","தேவ","ராட்சத","ராட்சத","மனுஷ","மனுஷ","தேவ"]


@app.route("/calc_from_spudam", methods=["POST"])
def calc_from_spudam():
    """கைமுறையாக உள்ளிட்ட ஸ்புடத்திலிருந்து வர்க்கம், அஷ்டவர்க்கம் கணக்கிட"""
    try:
        data = request.get_json(silent=True) or {}
        longs = {}
        for g, v in (data.get("longitudes") or {}).items():
            longs[g] = float(v) % 360
        if not longs:
            return jsonify({"status":"error","message":"ஸ்புடம் இல்லை"})

        vargas = ae.compute_all_vargas(longs)
        varga_charts = []
        for vkey in ["D1","D2","D3","D4","D5","D6","D7","D8","D9","D10","D11","D12","D15","D16","D18","D20","D22","D24","D27","D30","D36","D40","D45","D60","D144"]:
            if vkey not in vargas:
                continue
            varga_charts.append({"name": ae.VARGA_NAMES_TA.get(vkey, vkey),
                                 "grid": ae.build_grid_from_signs(vargas[vkey])})

        signs = {g: int(v // 30) for g, v in longs.items()}
        bhinnas, sarva = ae.compute_ashtakavarga(signs)
        graha_names = {"Sun":"சூரியன்","Moon":"சந்திரன்","Mars":"செவ்வாய்","Mercury":"புதன்","Jupiter":"குரு","Venus":"சுக்கிரன்","Saturn":"சனி"}
        prasthara = {}
        for g_en, pts in bhinnas.items():
            prasthara[graha_names.get(g_en, g_en)] = {str(i+1): pts[i] for i in range(12)}

        try:
            _hh = ae.compute_own_house_highlights(longs)
            house_highlights = {str(k): v for k, v in _hh.items()}
        except Exception:
            house_highlights = {}
        return jsonify({"status":"success",
                        "varga_charts": varga_charts,
                        "ashtakavarga": {"sarva": sarva, "prasthara": prasthara},
                        "house_highlights": house_highlights,
                        "d2_methods": ae.compute_d2_all(longs),
                        "d3_methods": ae.compute_d3_all(longs),
                        "d16_methods": ae.compute_d16_all(longs)})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)})

@app.route("/get_basic_info", methods=["POST"])
def get_basic_info():
    try:
        data = request.get_json(silent=True) or {}
        dob = data.get("dob", "1979-10-05")
        tob = data.get("tob", "10:10:28")
        lat = float(data.get("lat", LAT))
        lon = float(data.get("lon", LON))
        y, mo, d = [int(x) for x in dob.split("-")]
        hh, mm, ss = _parse_tob(tob)
        hour_ist = hh + mm/60.0 + ss/3600.0

        longs, _ = ae.get_all_sidereal_longitudes(y, mo, d, hour_ist, lat, lon)
        moon = longs["Moon"]; sun = longs["Sun"]; lag = longs["Lagna"]

        nak_idx = int(moon // (360.0/27))
        pada = int((moon % (360.0/27)) // (360.0/108)) + 1
        moon_sign = int(moon // 30)
        lag_sign = int(lag // 30)

        diff = (moon - sun) % 360
        tithi_num = int(diff // 12) + 1
        paksha = "சுக்ல" if tithi_num <= 15 else "கிருஷ்ண"
        t_idx = (tithi_num - 1) % 15
        tithi_name = "அமாவாசை" if tithi_num == 30 else TITHI_TA[t_idx]

        yoga_idx = int(((sun + moon) % 360) // (360.0/27))
        kar_num = int(diff // 6)
        karana_name = KARANA_TA[(kar_num - 1) % 7] if kar_num > 0 else KARANA_TA[0]

        wd_en = datetime(y, mo, d).strftime("%A")
        wd_ta = WEEKDAY_TA.get(wd_en, wd_en)

        yogi_point = (sun + moon + 93.3333) % 360
        yogi_nak = int(yogi_point // (360.0/27))
        yogi_lord = NAK_LORD[yogi_nak]
        avayogi_nak = (yogi_nak + 5) % 27
        avayogi_lord = NAK_LORD[avayogi_nak]
        SIGN_LORD = ["Mars","Venus","Mercury","Moon","Sun","Mercury","Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
        yogi_sign = int(yogi_point // 30)
        duplicate_yogi = SIGN_LORD[yogi_sign]

        return jsonify({"status":"success", "info":{
            "dob_str": "%02d-%02d-%04d" % (d, mo, y),
            "tob_str": "%02d:%02d:%02d" % (hh, mm, ss),
            "weekday": wd_ta,
            "nakshatra": NAK_TA[nak_idx],
            "pada": pada,
            "moon_rasi": ae.SIGNS_TA[moon_sign],
            "lagna_rasi": ae.SIGNS_TA[lag_sign],
            "tithi": paksha + " " + tithi_name,
            "yoga": YOGA_TA[yoga_idx],
            "karana": karana_name,
            "yogi_nak": NAK_TA[yogi_nak],
            "yogi": ae.GRAHA_TA.get(yogi_lord, yogi_lord),
            "avayogi_nak": NAK_TA[avayogi_nak],
            "avayogi": ae.GRAHA_TA.get(avayogi_lord, avayogi_lord),
            "duplicate_yogi": ae.GRAHA_TA.get(duplicate_yogi, duplicate_yogi),
            "yoni": YONI_TA[nak_idx],
            "hora": _compute_hora(y, mo, d, hour_ist, lat, lon, wd_en) or "-",
            "pakshi": _compute_pakshi(nak_idx, tithi_num <= 15),
            "vriksha": VRIKSHA_TA[nak_idx],
            "gana": GANA_TA[nak_idx],
        }})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)})

@app.route("/get_kochara", methods=["POST"])
def get_kochara():
    """இன்றைய கோச்சார நிலை + ஜென்ம கட்டத்துடன் ஒப்பீடு"""
    try:
        data = request.get_json(silent=True) or {}
        dob = data.get("dob", "1979-10-05")
        tob = data.get("tob", "10:10:28")
        lat = float(data.get("lat", LAT))
        lon = float(data.get("lon", LON))
        by, bmo, bd = [int(x) for x in dob.split("-")]
        bh, bmi, bs = _parse_tob(tob)

        natal_longs, _ = ae.get_all_sidereal_longitudes(
            by, bmo, bd, bh + bmi/60.0 + bs/3600.0, lat, lon)
        natal_signs = {g: int(v // 30) for g, v in natal_longs.items() if v is not None}
        moon_sign = natal_signs.get("Moon", 0)
        lagna_sign = natal_signs.get("Lagna", 0)

        now = now_ist()
        tr_longs, _ = ae.get_all_sidereal_longitudes(
            now.year, now.month, now.day,
            now.hour + now.minute/60.0 + now.second/3600.0, lat, lon)
        tr_signs = {g: int(v // 30) for g, v in tr_longs.items() if v is not None}

        bhinnas, sarva = ae.compute_ashtakavarga(natal_signs)
        OWN = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],
               "Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10]}

        out = {}
        for g_en in ["Lagna","Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]:
            if g_en not in tr_signs:
                continue
            tsg = tr_signs[g_en]
            own = OWN.get(g_en, [])
            from_own = min((((tsg - s) % 12) + 1) for s in own) if own else None
            out[g_en] = {
                "lord_ta": ae.GRAHA_TA.get(g_en, g_en),
                "rasi": ae.SIGNS_TA[tsg],
                "sarva": sarva[tsg] if sarva else 0,
                "bhinna": bhinnas.get(g_en, [0]*12)[tsg] if g_en in bhinnas else None,
                "from_moon": ((tsg - moon_sign) % 12) + 1,
                "from_lagna": ((tsg - lagna_sign) % 12) + 1,
                "from_own": from_own,
                "natal_rasi": ae.SIGNS_TA[natal_signs[g_en]] if g_en in natal_signs else None,
                "from_natal": ((tsg - natal_signs[g_en]) % 12) + 1 if g_en in natal_signs else None,
                "from_sun": ((tsg - natal_signs["Sun"]) % 12) + 1 if "Sun" in natal_signs else None,
                "from_each": {k: ((tsg - v) % 12) + 1 for k, v in natal_signs.items()},
            }
        tr_grid = ae.build_grid_from_signs(tr_signs)
        return jsonify({"status":"success",
                        "as_of": now.strftime("%d-%m-%Y %H:%M"),
                        "kochara": out,
                        "grid": tr_grid})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)})


@app.route("/export_all_charts", methods=["GET"])
def export_all_charts():
    """அனைத்து ஜாதகங்களையும் ஒரே JSON ஆக"""
    try:
        out = {}
        for f in os.listdir(SAVED_CHARTS_DIR):
            if f.endswith(".json"):
                with open(os.path.join(SAVED_CHARTS_DIR, f), encoding="utf-8") as fh:
                    out[f[:-5]] = json.load(fh)
        resp = make_response(_json.dumps({"version": 1, "charts": out}, ensure_ascii=False, indent=1))
        resp.headers["Content-Type"] = "application/json; charset=utf-8"
        resp.headers["Content-Disposition"] = "attachment; filename=jathagam_backup.json"
        return resp
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/import_charts", methods=["POST"])
def import_charts():
    """JSON backup-இலிருந்து ஜாதகங்களை மீட்டெடு"""
    try:
        data = request.get_json(silent=True) or {}
        charts = data.get("charts") or {}
        n = 0
        for name, cdata in charts.items():
            safe = "".join(ch for ch in str(name) if ch not in '/\\:*?"<>|').strip()
            if not safe:
                continue
            with open(os.path.join(SAVED_CHARTS_DIR, safe + ".json"), "w", encoding="utf-8") as fh:
                json.dump(cdata, fh, ensure_ascii=False)
            n += 1
        return jsonify({"status": "success", "imported": n})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/list_charts",methods=["GET"])
def list_charts():
    try:
        files=[f for f in os.listdir(SAVED_CHARTS_DIR) if f.endswith(".json")]
        names=[f[:-5] for f in files]
        return jsonify({"status":"success","charts":sorted(names)})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)})

@app.route("/save_chart",methods=["POST"])
def save_chart():
    data=request.get_json(silent=True) or {}
    name=data.get("name","").strip()
    if not name: return jsonify({"status":"error","message":"Name required"})
    chart_data=data.get("data")
    if not chart_data:
        chart_data={k:v for k,v in data.items() if k!="name"}
    path=os.path.join(SAVED_CHARTS_DIR,name+".json")
    try:
        with open(path,"w",encoding="utf-8") as f:
            json.dump(chart_data,f,ensure_ascii=False)
        try:
            import subprocess
            subprocess.Popen(["python3","backup_to_github.py"],
                             cwd=os.path.dirname(os.path.abspath(__file__)),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        return jsonify({"status":"success"})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)})

@app.route("/get_chart/<name>",methods=["GET"])
def get_chart(name):
    path=os.path.join(SAVED_CHARTS_DIR,name+".json")
    if not os.path.exists(path):
        return jsonify({"status":"error","message":"Not found"})
    try:
        with open(path,"r",encoding="utf-8") as f:
            chart_data=json.load(f)
        return jsonify({"status":"success","data":chart_data})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)})

@app.route("/delete_chart/<name>",methods=["DELETE"])
def delete_chart(name):
    path=os.path.join(SAVED_CHARTS_DIR,name+".json")
    if not os.path.exists(path):
        return jsonify({"status":"error","message":"Not found"})
    try:
        os.remove(path)
        return jsonify({"status":"success"})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)})

try:
    import subprocess as _sp
    _sp.run(["python3", "backup_to_github.py", "restore"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            timeout=25, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
except Exception:
    pass

if __name__=="__main__":
    app.run(host="0.0.0.0",port=8080,debug=True)
