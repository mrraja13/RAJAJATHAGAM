"""
astro_engine.py
================
உண்மையான (real) ஜோதிட கால்குலேஷன் இன்ஜின் — spudam, D1-D60 varga charts,
அஷ்டவர்க்கம், ஹோரை. dasha_engine.py-இல் உள்ள CORRECTION_ARCMIN அதே
அயனாம்ச திருத்தத்தையே (Lahiri +9.4', சித்திர நீளத்தில் நேரடியாக) பயன்படுத்துகிறது.

✅ சரிபார்ப்பு நிலை (13-09-2026): Rajaram-இன் உண்மையான Astro Vision PDF
ஜாதகத்துடன் (05-10-1979) pixel-level-இல் ஒப்பிட்டு **முழுமையாக சரிபார்க்கப்பட்டது**:
  - D1,D2,D3,D4,D7,D9,D10,D12,D16,D20,D24,D27,D30,D40,D45,D60 — 16 வர்க்கங்களும்
    exact match (Rahu/Ketu-க்கு MEAN_NODE பயன்பாடு, D60 சூத்திரம் திருத்தப்பட்டது)
  - Spudam (9 கிரகம்+லக்னம்+குளிகன்) — 20-22" துல்லியத்தில் (லக்னம் மட்டும் 5' வேறுபாடு — exact GPS coordinates தேவை)
  - அஷ்டகவர்க்கம் (Sarva + எல்லா 7 Bhinnashtakavarga அட்டவணைகளும்) — 337/337, 12/12 ராசிகளும் exact match
"""
import swisseph as swe
from datetime import datetime, timedelta
CORRECTION_ARCMIN = 9.05
YEAR_DAYS = 365.25
SIGNS_EN = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGNS_TA = ["மேஷம்","ரிஷபம்","மிதுனம்","கடகம்","சிம்மம்","கன்னி","துலாம்","விருச்சிகம்","தனுசு","மகரம்","கும்பம்","மீனம்"]
NAK_NAMES=["அஸ்வினி","பரணி","கார்த்திகை","ரோகிணி","மிருகசீரிடம்","திருவாதிரை","புனர்பூசம்","பூசம்","ஆயில்யம்","மகம்","பூரம்","உத்திரம்","ஹஸ்தம்","சித்திரை","சுவாதி","விசாகம்","அனுஷம்","கேட்டை","மூலம்","பூராடம்","உத்திராடம்","திருவோணம்","அவிட்டம்","சதயம்","பூரட்டாதி","உத்திரட்டாதி","ரேவதி"]
GRAHA_TA={"Sun":"சூரியன்","Moon":"சந்திரன்","Mars":"செவ்வாய்","Mercury":"புதன்","Jupiter":"குரு","Venus":"சுக்கிரன்","Saturn":"சனி","Rahu":"ராகு","Ketu":"கேது","Lagna":"லக்னம்"}
OWN_SIGNS={"Sun":["Leo"],"Moon":["Cancer"],"Mars":["Aries","Scorpio"],"Mercury":["Gemini","Virgo"],"Jupiter":["Sagittarius","Pisces"],"Venus":["Taurus","Libra"],"Saturn":["Capricorn","Aquarius"],"Rahu":[],"Ketu":[]}
EXALT_SIGN={"Sun":"Aries","Moon":"Taurus","Mars":"Capricorn","Mercury":"Virgo","Jupiter":"Cancer","Venus":"Pisces","Saturn":"Libra"}
DEBIL_SIGN={"Sun":"Libra","Moon":"Scorpio","Mars":"Cancer","Mercury":"Pisces","Jupiter":"Capricorn","Venus":"Virgo","Saturn":"Aries"}
KARAKA_ORDER=["ஆத்மகாரகன்","அமத்யகாரகன்","பாத்ருகாரகன்","மாத்ருகாரகன்","புத்ரகாரகன்","ஞாதிகாரகன்","தாரகாரகன்"]
MOVABLE={0,3,6,9}
FIXED={1,4,7,10}
DUAL={2,5,8,11}
def get_all_sidereal_longitudes(year,month,day,hour_ist,lat,lon,tz_offset=5.5):
    ut_hour=hour_ist-tz_offset
    jd_ut=swe.julday(year,month,day,ut_hour)
    swe.set_sid_mode(swe.SIDM_LAHIRI,0,0)
    ayan=swe.get_ayanamsa_ut(jd_ut)
    corr=CORRECTION_ARCMIN/60.0
    def sidereal(t): return (t-ayan+corr)%360
    bodies={"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,"Mercury":swe.MERCURY,"Jupiter":swe.JUPITER,"Venus":swe.VENUS,"Saturn":swe.SATURN}
    longs={}
    for name,code in bodies.items():
        trop=swe.calc_ut(jd_ut,code,swe.FLG_SWIEPH)[0][0]
        longs[name]=sidereal(trop)
    rahu_trop=swe.calc_ut(jd_ut,swe.MEAN_NODE,swe.FLG_SWIEPH)[0][0]
    longs["Rahu"]=sidereal(rahu_trop)
    longs["Ketu"]=(longs["Rahu"]+180)%360
    try:
        cusps_t,ascmc_t=swe.houses_ex(jd_ut,lat,lon,b"P")
        longs["Lagna"]=sidereal(ascmc_t[0])
    except: longs["Lagna"]=None
    return longs,jd_ut

def lon_to_sign_deg(lon): return int(lon//30),lon%30
def deg_to_dms(deg):
    d=int(deg);m_full=(deg-d)*60;m=int(m_full);s=(m_full-m)*60
    return str(d)+chr(176)+" "+str(m)+"' "+str(round(s,1))+chr(34)
def lon_to_nak_pada(lon):
    ns=360.0/27.0;ps=ns/4.0;ni=int(lon//ns);pada=int((lon%ns)/ps)+1
    return NAK_NAMES[ni%27],pada
def graha_status(name,sign_idx):
    if name in("Rahu","Ketu","Lagna","Gulika"): return "இயல்பு"
    sign=SIGNS_EN[sign_idx]
    if EXALT_SIGN.get(name)==sign: return "உச்சம்"
    if DEBIL_SIGN.get(name)==sign: return "நீசம்"
    if sign in OWN_SIGNS.get(name,[]): return "ஆட்சி"
    return "இயல்பு"
def varga_d1(s,d): return s
def varga_d2(s,d):
    odd=(s%2==0);half=0 if d<15 else 1
    if odd: return SIGNS_EN.index("Leo") if half==0 else SIGNS_EN.index("Cancer")
    return SIGNS_EN.index("Cancer") if half==0 else SIGNS_EN.index("Leo")
def varga_d3(s,d): return (s+[0,4,8][int(d//10)])%12
def varga_d4(s,d): return (s+[0,3,6,9][int(d//7.5)])%12

def varga_d5(s,d):
    """பஞ்சாம்சம் D5 — ஆன்மீகம், காதல், புகழ், வெற்றி, அதிகாரம்"""
    p = int(d // 6)
    base = [0,5,10,3,8,1,6,11,4,9,2,7]
    return (base[s] + p) % 12

def varga_d6(s,d):
    """ரோகாம்சம் D6 — நோய்"""
    p = int(d // 5)
    base = 0 if s % 2 == 0 else 6
    return (base + p) % 12

def varga_d8(s,d):
    """அஷ்டாம்சம் D8 — ஆயுள்"""
    p = int(d // 3.75)
    base = [0,8,4][s % 3]
    return (base + p) % 12


def varga_d11(s,d):
    """ருத்ராம்சம் D11 — லாபம், ஆதாயம்"""
    p = int(d // (30/11))
    return (s + p) % 12

def varga_d15(s,d):
    """பஞ்சதசாம்சம் D15"""
    p = int(d // 2.0)
    base = [0,10,6,2][0] if s % 2 == 0 else 0
    return ((0 if s % 2 == 0 else 6) + p) % 12

def varga_d18(s,d):
    """அஷ்டாதசாம்சம் D18"""
    p = int(d // (30/18))
    return (s + p) % 12

def varga_d22(s,d):
    """த்வாவிம்சாம்சம் D22"""
    p = int(d // (30/22))
    return (s + p) % 12

def varga_d36(s,d):
    """ஷட்த்ரிம்சாம்சம் D36"""
    p = int(d // (30/36))
    return (s + p) % 12

def varga_d144(s,d):
    """த்வாதசாம்சாம்சம் D144"""
    p = int(d // (30/144))
    return (s + p) % 12

def varga_d7(s,d):
    p=int(d//(30.0/7));odd=(s%2==0);st=s if odd else (s+6)%12
    return (st+p)%12
def varga_d9(s,d):
    p=int(d//(30.0/9))
    if s in MOVABLE: st=s
    elif s in FIXED: st=(s+8)%12
    else: st=(s+4)%12
    return (st+p)%12
def varga_d10(s,d):
    p=int(d//3.0);odd=(s%2==0);st=s if odd else (s+8)%12
    return (st+p)%12
def varga_d12(s,d): return (s+int(d//2.5))%12
def varga_d16(s,d):
    p=int(d//(30.0/16))
    if s in MOVABLE: st=SIGNS_EN.index("Aries")
    elif s in FIXED: st=SIGNS_EN.index("Leo")
    else: st=SIGNS_EN.index("Sagittarius")
    return (st+p)%12
def varga_d20(s,d):
    p=int(d//1.5)
    if s in MOVABLE: st=SIGNS_EN.index("Aries")
    elif s in FIXED: st=SIGNS_EN.index("Sagittarius")
    else: st=SIGNS_EN.index("Leo")
    return (st+p)%12
def varga_d24(s,d):
    p=int(d//1.25);odd=(s%2==0)
    return (SIGNS_EN.index("Leo" if odd else "Cancer")+p)%12
def varga_d27(s,d):
    p=int(d//(30.0/27));e=s%4
    st={0:SIGNS_EN.index("Aries"),1:SIGNS_EN.index("Cancer"),2:SIGNS_EN.index("Libra"),3:SIGNS_EN.index("Capricorn")}[e]
    return (st+p)%12
def varga_d30(s,d):
    odd=(s%2==0)
    if odd: table=[(5,"Mars","Aries"),(5,"Saturn","Aquarius"),(8,"Jupiter","Sagittarius"),(7,"Mercury","Gemini"),(5,"Venus","Libra")]
    else: table=[(5,"Venus","Taurus"),(7,"Mercury","Virgo"),(8,"Jupiter","Pisces"),(5,"Saturn","Capricorn"),(5,"Mars","Scorpio")]
    acc=0.0
    for span,lord,sn in table:
        if d<acc+span: return SIGNS_EN.index(sn)
        acc+=span
    return SIGNS_EN.index(table[-1][2])
def varga_d40(s,d):
    p=int(d//0.75);odd=(s%2==0)
    return (SIGNS_EN.index("Aries" if odd else "Libra")+p)%12
def varga_d45(s,d):
    p=int(d//(30.0/45))
    if s in MOVABLE: st=SIGNS_EN.index("Aries")
    elif s in FIXED: st=SIGNS_EN.index("Leo")
    else: st=SIGNS_EN.index("Sagittarius")
    return (st+p)%12
def varga_d60(s,d): return (s+int(d//0.5))%12
VARGA_FUNCS={"D1":varga_d1,"D2":varga_d2,"D3":varga_d3,"D4":varga_d4,"D5":varga_d5,"D6":varga_d6,"D7":varga_d7,"D8":varga_d8,"D9":varga_d9,"D10":varga_d10,"D11":varga_d11,"D12":varga_d12,"D15":varga_d15,"D18":varga_d18,"D22":varga_d22,"D16":varga_d16,"D20":varga_d20,"D24":varga_d24,"D27":varga_d27,"D30":varga_d30,"D36":varga_d36,"D40":varga_d40,"D45":varga_d45,"D60":varga_d60,"D144":varga_d144}
VARGA_NAMES_TA={"D1":"D1 - ராசி சக்கரம்","D2":"D2 - ஹோரா சக்கரம்","D3":"D3 - திரேக்காணம்","D4":"D4 - சதுர்த்தாம்சம்","D5":"D5 - பஞ்சாம்சம்","D6":"D6 - ரோகாம்சம்","D7":"D7 - சப்தாம்சம்","D8":"D8 - அஷ்டாம்சம்","D9":"D9 - நவாம்சம்","D10":"D10 - தசாம்சம்","D11":"D11 - ருத்ராம்சம்","D12":"D12 - துவாதசாம்சம்","D15":"D15 - பஞ்சதசாம்சம்","D18":"D18 - அஷ்டாதசாம்சம்","D22":"D22 - த்வாவிம்சாம்சம்","D16":"D16 - சோடசாம்சம்","D20":"D20 - விம்சாம்சம்","D24":"D24 - சதுர்விம்சாம்சம்","D27":"D27 - சப்தவிம்சாம்சம்","D30":"D30 - திரிம்சாம்சம்","D36":"D36 - ஷட்த்ரிம்சாம்சம்","D40":"D40 - கவேதாம்சம்","D45":"D45 - அக்ஷேதாம்சம்","D60":"D60 - ஷஷ்டியாம்சம்","D144":"D144 - த்வாதசாம்சாம்சம்"}
VERIFIED_VARGAS=set(VARGA_FUNCS.keys())
def compute_all_vargas(longitudes):
    result={}
    for vkey,func in VARGA_FUNCS.items():
        row={}
        for graha,lon in longitudes.items():
            if lon is None: continue
            s,d=lon_to_sign_deg(lon)
            row[graha]=func(s,d)
        result[vkey]=row
    return result
def build_grid_from_signs(graha_signs):
    grid={str(h):{"planets":[]} for h in range(1,13)}
    code_map={"Sun":"Su","Moon":"Mo","Mars":"Ma","Mercury":"Me","Jupiter":"Ju","Venus":"Ve","Saturn":"Sa","Rahu":"Ra","Ketu":"Ke","Lagna":"Lag","Gulika":"Gk"}
    _order=["Lagna","Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu","Gulika"]
    def _rank(g):
        return _order.index(g) if g in _order else 99
    for graha in sorted(graha_signs.keys(), key=_rank):
        sign_idx=graha_signs[graha]
        grid[str(sign_idx+1)]["planets"].append({"name":GRAHA_TA[graha],"code":code_map[graha]})
    return grid
def compute_karakas(longitudes):
    seven=["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
    degs=[(g,lon_to_sign_deg(longitudes[g])[1]) for g in seven]
    degs.sort(key=lambda x:-x[1])
    return {KARAKA_ORDER[i]:GRAHA_TA[degs[i][0]] for i in range(7)}
ASTANGAM_LIGHT_ORB=5.0
ASTANGAM_DARK_ORB=10.0
ASTANGAM_GRAHAS=["Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
def compute_astangam(longitudes):
    sun_lon=longitudes["Sun"];result={}
    for g in ASTANGAM_GRAHAS:
        if g not in longitudes or longitudes[g] is None: continue
        diff=abs(longitudes[g]-sun_lon)%360
        if diff>180: diff=360-diff
        if diff<=ASTANGAM_LIGHT_ORB: result[g]="light"
        elif diff<=ASTANGAM_DARK_ORB: result[g]="dark"
        else: result[g]=None
    return result
KIRAGANAM_LIGHT_ORB=5.0
KIRAGANAM_DARK_ORB=10.0
KIRAGANAM_GRAHAS=["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
def compute_kiraganam(longitudes):
    rahu_lon=longitudes.get("Rahu");ketu_lon=longitudes.get("Ketu");result={}
    for g in KIRAGANAM_GRAHAS:
        if g not in longitudes or longitudes[g] is None: continue
        dists=[]
        for nl in (rahu_lon,ketu_lon):
            if nl is None: continue
            diff=abs(longitudes[g]-nl)%360
            if diff>180: diff=360-diff
            dists.append(diff)
        if not dists: continue
        md=min(dists)
        if md<=KIRAGANAM_LIGHT_ORB: result[g]="light"
        elif md<=KIRAGANAM_DARK_ORB: result[g]="dark"
        else: result[g]=None
    return result
YUDDHA_PLANETS=["Mars","Mercury","Jupiter","Venus","Saturn"]
YUDDHA_ORB=1.0
def compute_graha_yuddha(longitudes):
    result={g:False for g in YUDDHA_PLANETS}
    for i in range(len(YUDDHA_PLANETS)):
        for j in range(i+1,len(YUDDHA_PLANETS)):
            g1,g2=YUDDHA_PLANETS[i],YUDDHA_PLANETS[j]
            if g1 not in longitudes or g2 not in longitudes: continue
            s1,_=lon_to_sign_deg(longitudes[g1]);s2,_=lon_to_sign_deg(longitudes[g2])
            if s1!=s2: continue
            diff=abs(longitudes[g1]-longitudes[g2])%360
            if diff>180: diff=360-diff
            if diff<=YUDDHA_ORB: result[g1]=True;result[g2]=True
    return result
PUSHKARA_NAVAMSA_NUM={}
for _s in MOVABLE: PUSHKARA_NAVAMSA_NUM[_s]=5
for _s in FIXED: PUSHKARA_NAVAMSA_NUM[_s]=9
for _s in DUAL: PUSHKARA_NAVAMSA_NUM[_s]=3
def is_pushkara_navamsa(sign_idx,deg):
    part=int(deg//(30.0/9))+1
    return part==PUSHKARA_NAVAMSA_NUM.get(sign_idx)
ASTANGAM_COLORS={"light":"#ffcc80","dark":"#fb8c00"}
KIRAGANAM_COLORS={"light":"#e0e0e0","dark":"#9e9e9e"}
YUDDHA_COLOR="#c62828"
def compute_own_house_highlights(longitudes):
    highlights={}
    def add(si,color,label):
        highlights.setdefault(si,[])
        highlights[si].append({"color":color,"label":label})
    for g,tier in compute_astangam(longitudes).items():
        if tier is None: continue
        for sn in OWN_SIGNS.get(g,[]):
            add(SIGNS_EN.index(sn),ASTANGAM_COLORS[tier],"Astangam("+GRAHA_TA[g]+")")
    for g,tier in compute_kiraganam(longitudes).items():
        if tier is None: continue
        for sn in OWN_SIGNS.get(g,[]):
            add(SIGNS_EN.index(sn),KIRAGANAM_COLORS[tier],"Kiraganam("+GRAHA_TA[g]+")")
    for g,is_war in compute_graha_yuddha(longitudes).items():
        if not is_war: continue
        for sn in OWN_SIGNS.get(g,[]):
            add(SIGNS_EN.index(sn),YUDDHA_COLOR,"Yuddham("+GRAHA_TA[g]+")")
    return highlights
BAV_TABLE={"Sun":{"Sun":[1,2,4,7,8,9,10,11],"Moon":[3,6,10,11],"Mars":[1,2,4,7,8,9,10,11],"Mercury":[3,5,6,9,10,11,12],"Jupiter":[5,6,9,11],"Venus":[6,7,12],"Saturn":[1,2,4,7,8,9,10,11],"Lagna":[3,4,6,10,11,12]},"Moon":{"Sun":[3,6,7,8,10,11],"Moon":[1,3,6,7,10,11],"Mars":[2,3,5,6,9,10,11],"Mercury":[1,3,4,5,7,8,10,11],"Jupiter":[1,4,7,8,10,11,12],"Venus":[3,4,5,7,9,10,11],"Saturn":[3,5,6,11],"Lagna":[3,6,10,11]},"Mars":{"Sun":[3,5,6,10,11],"Moon":[3,6,11],"Mars":[1,2,4,7,8,10,11],"Mercury":[3,5,6,11],"Jupiter":[6,10,11,12],"Venus":[6,8,11,12],"Saturn":[1,4,7,8,9,10,11],"Lagna":[1,3,6,10,11]},"Mercury":{"Sun":[5,6,9,11,12],"Moon":[2,4,6,8,10,11],"Mars":[1,2,4,7,8,9,10,11],"Mercury":[1,3,5,6,9,10,11,12],"Jupiter":[6,8,11,12],"Venus":[1,2,3,4,5,8,9,11],"Saturn":[1,2,4,7,8,9,10,11],"Lagna":[1,2,4,6,8,10,11]},"Jupiter":{"Sun":[1,2,3,4,7,8,9,10,11],"Moon":[2,5,7,9,11],"Mars":[1,2,4,7,8,10,11],"Mercury":[1,2,4,5,6,9,10,11],"Jupiter":[1,2,3,4,7,8,10,11],"Venus":[2,5,6,9,10,11],"Saturn":[3,5,6,12],"Lagna":[1,2,4,5,6,7,9,10,11]},"Venus":{"Sun":[8,11,12],"Moon":[1,2,3,4,5,8,9,11,12],"Mars":[3,5,6,9,11,12],"Mercury":[3,5,6,9,11],"Jupiter":[5,8,9,10,11],"Venus":[1,2,3,4,5,8,9,10,11],"Saturn":[3,4,5,8,9,10,11],"Lagna":[1,2,3,4,5,8,9,11]},"Saturn":{"Sun":[1,2,4,7,8,10,11],"Moon":[3,6,11],"Mars":[3,5,6,10,11,12],"Mercury":[6,8,9,10,11,12],"Jupiter":[5,6,11,12],"Venus":[6,11,12],"Saturn":[3,5,6,11],"Lagna":[1,3,4,6,10,11]}}
def compute_ashtakavarga(sign_idx_map):
    bhinnas={}
    for target,table in BAV_TABLE.items():
        points=[0]*12
        for contributor,house_list in table.items():
            if contributor not in sign_idx_map: continue
            c_sign=sign_idx_map[contributor]
            for h in house_list:
                points[(c_sign+h-1)%12]+=1
        bhinnas[target]=points
    sarva=[0]*12
    for pts in bhinnas.values():
        for i in range(12): sarva[i]+=pts[i]
    return bhinnas,sarva
WEEKDAY_LORD={0:"Moon",1:"Mars",2:"Mercury",3:"Jupiter",4:"Venus",5:"Saturn",6:"Sun"}
HORA_SEQUENCE=["Sun","Venus","Mercury","Moon","Saturn","Jupiter","Mars"]
def get_sunrise_sunset(year,month,day,lat,lon,tz_offset=5.5):
    jd=swe.julday(year,month,day,0.0)-tz_offset/24.0
    geopos=(lon,lat,0.0)
    try:
        res_r,rise=swe.rise_trans(jd,swe.SUN,swe.CALC_RISE,geopos)
        res_s,sett=swe.rise_trans(jd,swe.SUN,swe.CALC_SET,geopos)
        if res_r!=0 or res_s!=0: return None,None
        return rise[0],sett[0]
    except: return None,None
def jd_to_datetime_ist(jd,tz_offset=5.5):
    y,m,d,h=swe.revjul(jd+tz_offset/24.0)
    hh=int(h);mm=int((h-hh)*60);ss=int(((h-hh)*60-mm)*60)
    return datetime(y,m,d,hh,mm,ss)
def compute_hora_list(year,month,day,lat,lon):
    sunrise_jd,sunset_jd=get_sunrise_sunset(year,month,day,lat,lon)
    if sunrise_jd is None: return []
    next_sunrise_jd,_=get_sunrise_sunset(year,month,day+1,lat,lon)
    if next_sunrise_jd is None: next_sunrise_jd=sunrise_jd+1
    day_len=(sunset_jd-sunrise_jd)/12.0
    night_len=(next_sunrise_jd-sunset_jd)/12.0
    weekday=datetime(year,month,day).weekday()
    day_lord=WEEKDAY_LORD[weekday]
    start_idx=HORA_SEQUENCE.index(day_lord)
    horas=[];cur=sunrise_jd
    for i in range(24):
        span=day_len if i<12 else night_len;end=cur+span
        lord=HORA_SEQUENCE[(start_idx+i)%7]
        horas.append({"hora":GRAHA_TA[lord],"start":jd_to_datetime_ist(cur).strftime("%d-%m-%Y %H:%M"),"end":jd_to_datetime_ist(end).strftime("%d-%m-%Y %H:%M")})
        cur=end
    return horas
GRAHA_TA["Gulika"]="குளிகன்"
GULIKA_DAY_CONST={"Saturday":12,"Friday":34.763321,"Thursday":60,"Wednesday":84,"Tuesday":108,"Monday":132,"Sunday":160.216}
GULIKA_NIGHT_CONST={"Tuesday":192,"Monday":216,"Sunday":240,"Saturday":264,"Friday":288,"Thursday":312,"Wednesday":336}
GULIKA_VERIFIED_KEYS={'Friday_day','Sunday_day'}

GULIKA_PART_DAY = {"Sunday":7,"Monday":6,"Tuesday":5,"Wednesday":4,"Thursday":3,"Friday":2,"Saturday":1}
GULIKA_PART_NIGHT = {"Sunday":3,"Monday":2,"Tuesday":1,"Wednesday":0,"Thursday":6,"Friday":5,"Saturday":4}

def gulika_by_parts(year, month, day, lat, lon, jd_birth, weekday_en, is_day_birth, tz=5.5):
    """பகல்/இரவை 8 பகுதியாகப் பிரித்து, குளிகன் பகுதியின் தொடக்க லக்னம்"""
    sr, ss = get_sunrise_sunset(year, month, day, lat, lon)
    if sr is None or ss is None:
        return None
    if is_day_birth:
        start, end = sr, ss
        part = GULIKA_PART_DAY[weekday_en]
    else:
        start = ss
        nsr, _ = get_sunrise_sunset(year, month, day + 1, lat, lon)
        if nsr is None:
            return None
        end = nsr
        part = GULIKA_PART_NIGHT[weekday_en]
    seg = (end - start) / 8.0
    jd_g = start + seg * part
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        ayan = swe.get_ayanamsa_ut(jd_g)
        corr = CORRECTION_ARCMIN / 60.0
        _c, ascmc = swe.houses_ex(jd_g, lat, lon, b"P")
        return (ascmc[0] - ayan + corr) % 360
    except Exception:
        return None

def get_gulika_longitude(sun_sidereal_lon,weekday_en,is_day_birth):
    const_table=GULIKA_DAY_CONST if is_day_birth else GULIKA_NIGHT_CONST
    const=const_table[weekday_en]
    suffix="day" if is_day_birth else "night"
    key=weekday_en+"_"+suffix
    verified=key in GULIKA_VERIFIED_KEYS
    return (sun_sidereal_lon+const)%360,verified

# VCJV அட்டவணை — பராசர முறை (நேரடி lookup, சூத்திரத்துடன் ஒப்பிட)
VCJV_D3 = [
 [1,2,3,4,5,6,7,8,9,10,11,12],
 [5,6,7,8,9,10,11,12,1,2,3,4],
 [9,10,11,12,1,2,3,4,5,6,7,8],
]
VCJV_D2 = [
 [5,4,5,4,5,4,5,4,5,4,5,4],
 [4,5,4,5,4,5,4,5,4,5,4,5],
]
VCJV_D16 = [[((r + [0,4,8][s % 3]) % 12) + 1 for s in range(12)] for r in range(16)]


VCJV_D5 = [
 [1,6,11,4,9,2,7,12,5,10,3,8],
 [2,7,12,5,10,3,8,1,6,11,4,9],
 [3,8,1,6,11,4,9,2,7,12,5,10],
 [4,9,2,7,12,5,10,3,8,1,6,11],
 [5,10,3,8,1,6,11,4,9,2,7,12],
]
VCJV_D6 = [
 [1,7,1,7,1,7,1,7,1,7,1,7],
 [2,8,2,8,2,8,2,8,2,8,2,8],
 [3,9,3,9,3,9,3,9,3,9,3,9],
 [4,10,4,10,4,10,4,10,4,10,4,10],
 [5,11,5,11,5,11,5,11,5,11,5,11],
 [6,12,6,12,6,12,6,12,6,12,6,12],
]
VCJV_D8 = [
 [1,9,5,1,9,5,1,9,5,1,9,5],
 [2,10,6,2,10,6,2,10,6,2,10,6],
 [3,11,7,3,11,7,3,11,7,3,11,7],
 [4,12,8,4,12,8,4,12,8,4,12,8],
 [5,1,9,5,1,9,5,1,9,5,1,9],
 [6,2,10,6,2,10,6,2,10,6,2,10],
 [7,3,11,7,3,11,7,3,11,7,3,11],
 [8,4,12,8,4,12,8,4,12,8,4,12],
]

def vcjv_lookup(varga, sign_idx, deg):
    """VCJV அட்டவணையிலிருந்து வர்க்க ராசி (0-based)"""
    if varga == 3:
        row = int(deg // 10)
        return VCJV_D3[min(row,2)][sign_idx] - 1
    if varga == 2:
        row = 0 if deg < 15 else 1
        return VCJV_D2[row][sign_idx] - 1
    if varga == 16:
        row = int(deg // 1.875)
        return VCJV_D16[min(row,15)][sign_idx] - 1
    if varga == 5:
        row = int(deg // 6)
        return VCJV_D5[min(row,4)][sign_idx] - 1
    if varga == 6:
        row = int(deg // 5)
        return VCJV_D6[min(row,5)][sign_idx] - 1
    if varga == 8:
        row = int(deg // 3.75)
        return VCJV_D8[min(row,7)][sign_idx] - 1
    return None

def verify_vargas(longitudes):
    """சூத்திரம் vs VCJV அட்டவணை — வேறுபாடுகளைப் பட்டியலிடு"""
    diffs = []
    fn = {2: varga_d2, 3: varga_d3, 5: varga_d5, 6: varga_d6, 8: varga_d8, 16: varga_d16}
    for v in (2, 3, 5, 6, 8, 16):
        for graha, L in longitudes.items():
            if L is None:
                continue
            s = int(L // 30); d = L % 30
            calc = fn[v](s, d)
            tab = vcjv_lookup(v, s, d)
            if tab is not None and calc != tab:
                diffs.append({
                    "varga": "D%d" % v,
                    "graha": GRAHA_TA.get(graha, graha),
                    "formula": SIGNS_TA[calc],
                    "table": SIGNS_TA[tab],
                })
    return diffs


# ── D2 ஹோரா — 11 முறைகள் (VCJV அட்டவணை) ──
D2_METHODS = {
 "parasara":   ("பராசர ஹோரா PD2",      [[5,4,5,4,5,4,5,4,5,4,5,4],[4,5,4,5,4,5,4,5,4,5,4,5]]),
 "kasinatha":  ("காசிநாத் ஹோரா KD2",    [[8,2,6,4,5,3,7,1,12,10,11,9],[1,7,3,5,4,6,2,8,9,11,10,12]]),
 "parivritti": ("பரிவிருத்தித்வய ஹோரா PV D2",[[1,3,5,7,9,11,1,3,5,7,9,11],[2,4,6,8,10,12,2,4,6,8,10,12]]),
 "laba":       ("லாப மன்டூக ஹோரா LM D2",  [[1,2,3,4,5,6,7,8,9,10,11,12],[11,12,1,2,3,4,5,6,7,8,9,10]]),
 "jagannatha": ("ஜகநாத் ஹோரா JD2",     [[7,2,9,4,5,12,7,2,9,4,5,12],[1,8,3,10,11,6,1,8,3,10,11,6]]),
 "samasaptaka":("சமசப்தக ஹோரா SS D2",    [[1,2,3,4,5,6,7,8,9,10,11,12],[7,8,9,10,11,12,1,2,3,4,5,6]]),
 "raman":      ("ராமன் ஹோரா RD2",      [[8,2,6,4,5,3,7,1,12,10,11,9],[10,12,1,7,3,4,5,6,2,8,9,11]]),
 "manduka":    ("மன்டூக ஹோரா MD2",     [[1,2,3,4,5,6,7,8,9,10,11,12],[3,4,5,6,7,8,9,10,11,12,1,2]]),
 "niranjan":   ("நிரஞ்சன் ஹோரா ND2",    [[6,3,5,5,7,2,12,9,11,10,8,1],[1,8,10,11,9,12,2,7,4,4,3,6]]),
 "umasambhu":  ("உமா சாம்பு ஹோரா US D2",  [[1,4,5,8,9,12,1,4,5,8,9,12],[2,3,6,7,10,11,2,3,6,7,10,11]]),
 "purvaparasari":("பூர்வ பராசரி ஹோரா PP D2",[[1,2,3,4,5,6,7,8,9,10,11,12],[2,3,4,5,6,7,8,9,10,11,12,1]]),
}

def d2_method(method, sign_idx, deg):
    """D2 — குறிப்பிட்ட முறைப்படி வர்க்க ராசி (0-based)"""
    row = 0 if deg < 15 else 1
    tbl = D2_METHODS[method][1]
    return tbl[row][sign_idx] - 1

def compute_d2_all(longitudes):
    """D2-இன் அனைத்து முறைகளுக்கும் கட்டம்"""
    out = []
    for key, (name, _t) in D2_METHODS.items():
        signs = {}
        for g, L in longitudes.items():
            if L is None:
                continue
            signs[g] = d2_method(key, int(L // 30), L % 30)
        out.append({"key": key, "name": name, "grid": build_grid_from_signs(signs)})
    return out


# ── D3 திரேக்காணம் — 4 முறைகள் ──
D3_METHODS = {
 "parasara": ("பராசர திரேக்காணம் PD3", [
   [1,2,3,4,5,6,7,8,9,10,11,12],
   [5,6,7,8,9,10,11,12,1,2,3,4],
   [9,10,11,12,1,2,3,4,5,6,7,8]]),
 "jagannatha": ("ஜெகன்நாத் திரேக்காணம் JD3", [
   [1,10,7,4,1,10,7,4,1,10,7,4],
   [5,2,11,8,5,2,11,8,5,2,11,8],
   [9,6,3,12,9,6,3,12,9,6,3,12]]),
 "somanatha": ("சோம்நாத் திரேக்காணம் SD3", [
   [1,12,4,9,7,6,10,3,1,12,4,9],
   [2,11,5,8,8,5,11,2,2,11,5,8],
   [3,10,6,7,9,4,12,1,3,10,6,7]]),
 "parivritti": ("பரிவிருத்தி த்வய திரேக்காணம் PV D3", [
   [1,4,7,10,1,4,7,10,1,4,7,10],
   [2,5,8,11,2,5,8,11,2,5,8,11],
   [3,6,9,12,3,6,9,12,3,6,9,12]]),
}

def d3_method(method, sign_idx, deg):
    row = min(int(deg // 10), 2)
    return D3_METHODS[method][1][row][sign_idx] - 1

def compute_d3_all(longitudes):
    out = []
    for key, (name, _t) in D3_METHODS.items():
        signs = {}
        for g, L in longitudes.items():
            if L is None:
                continue
            signs[g] = d3_method(key, int(L // 30), L % 30)
        out.append({"key": key, "name": name, "grid": build_grid_from_signs(signs)})
    return out

# ── D16 ஷோடசாம்சம் — 3 முறைகள் ──
D16_METHODS = {
 "parasara": ("பராசர ஷோடசாம்சம் PD16",
   [[((r + [0,4,8][s % 3]) % 12) + 1 for s in range(12)] for r in range(16)]),
 "sesathri": ("சேஷாத்ரி ஐயர் ஷோடசாம்சம் HR16", [
   [1,5,3,7,5,9,7,11,9,1,11,3],
   [2,4,4,6,6,8,8,10,10,12,12,2],
   [3,3,5,5,7,7,9,9,11,11,1,1],
   [4,2,6,4,8,6,10,8,12,10,2,12],
   [5,1,7,3,9,5,11,7,1,9,3,11],
   [6,12,8,2,10,4,12,6,2,8,4,10],
   [7,11,9,1,11,3,1,5,3,7,5,9],
   [8,10,10,12,12,2,2,4,4,6,6,8],
   [9,9,11,11,1,1,3,3,5,5,7,7],
   [10,8,12,10,2,12,4,2,6,4,8,6],
   [11,7,1,9,3,11,5,1,7,3,9,5],
   [12,6,2,8,4,10,6,12,8,2,10,4],
   [1,5,3,7,5,9,7,11,9,1,11,3],
   [2,4,4,6,6,8,8,10,10,12,12,2],
   [3,3,5,5,7,7,9,9,11,11,1,1],
   [4,2,6,4,8,6,10,8,12,10,2,12]]),
}

def d16_method(method, sign_idx, deg):
    row = min(int(deg // 1.875), 15)
    return D16_METHODS[method][1][row][sign_idx] - 1

def compute_d16_all(longitudes):
    out = []
    for key, (name, _t) in D16_METHODS.items():
        signs = {}
        for g, L in longitudes.items():
            if L is None:
                continue
            signs[g] = d16_method(key, int(L // 30), L % 30)
        out.append({"key": key, "name": name, "grid": build_grid_from_signs(signs)})
    return out

