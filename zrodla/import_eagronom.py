import xlrd, re, json, datetime as dt, sys
SRC = sys.argv[2] if len(sys.argv) > 2 else "plan.xls"  # eksport .xls z eAgronom; uzycie: python3 import_eagronom.py wynik.json plan.xls
b = xlrd.open_workbook(SRC)
season = b.sheets()[0].cell_value(0, 0)
m = re.search(r"(\d{4})/(\d{2})", season)
ROK = 2000 + int(m.group(2))  # rok zbioru = drugi rok sezonu

def num(v):
    if v in ("", None): return None
    try: return float(v)
    except: return None

def date(s):
    s = str(s).strip()
    ds = re.findall(r"(\d{1,2})\.(\d{2})\.(\d{4})", s)
    if ds:
        d, mo, y = ds[-1]
        if "–" in s or "-" in s:
            # zakres "25 – 26.09.2025" → pierwszy dzień
            first = re.match(r"\s*(\d{1,2})", s).group(1)
            return dt.date(int(y), int(mo), int(first)).isoformat(), s
        return dt.date(int(y), int(mo), int(d)).isoformat(), None
    return None, s

def dose(s):
    s = str(s).strip()
    if not s: return None, None
    m = re.match(r"([\d\s.,]+)\s*(.*)", s)
    if not m: return None, s
    val = float(m.group(1).replace(" ", "").replace(" ", "").replace(",", "."))
    unit = m.group(2).replace("/ha", "").strip()
    unit = {"Nasiona": "szt.", "nasiona": "szt."}.get(unit, unit)
    return val, unit

def crop(s):
    # "Pszenżyto ozime (Borowik C1)" / "Kukurydza (Farmoritz)(MP)" / "TUZ (regularnie odnawiane) (Zdecyduję później)"
    s = s.strip()
    parts = re.findall(r"\(([^)]*)\)", s)
    base = re.sub(r"\s*\([^)]*\)", "", s).strip()
    if base == "TUZ":
        return "TUZ (regularnie odnawiane)", "", ""
    odm = ""; extra = []
    for p in parts:
        if p == "Zdecyduję później": continue
        if p == "MP": extra.append("(MP) wg eAgronom"); continue
        odm = p
    return base, odm, "; ".join(extra)

def kind(name, typ):
    n = name.lower(); t = typ.lower()
    if "gnojowic" in n or "obornik" in n: return "Nawożenie organiczne"
    if "oprysk" in n or "środki ochrony" in n:
        if "adiuwant" in t: return "Adiuwant"
        for k in ("Herbicyd", "Fungicyd", "Insektycyd"):
            if k.lower() in t: return k
        return "Inny"
    if "siew" in n:
        return "Siew / sadzenie" if "nasiona" in t else "Nawożenie mineralne"
    if "nawożenie" in n: return "Nawożenie mineralne"
    if "kultywator" in n or "uprawa" in n: return "Uprawa przedsiewna"
    return "Inny"

pola, uprawy, zabiegi = [], [], []
for s in b.sheets():
    ident = str(s.cell_value(3, 1)).strip()
    nr = str(s.cell_value(4, 1)).strip()
    mm = re.match(r"(.*?)\s*\((.*)\)\s*$", nr)
    dzialki, name = (mm.group(1), mm.group(2)) if mm else (nr, s.name)
    name = re.sub(r"\s+", " ", name).strip()
    area = num(s.cell_value(4, 4)) or num(s.cell_value(5, 1))
    ph = num(s.cell_value(9, 1)); ph = ph if ph else None
    p2o5 = num(s.cell_value(10, 1)); k2o = num(s.cell_value(11, 1))
    ana, _ = date(s.cell_value(7, 1)) if s.cell_value(7, 1) else (None, None)
    pola.append(dict(name=name, dz=dzialki, ident=ident, area=area, ph=ph, p=p2o5, k=k2o, ana=ana))
    c, odm, ex = crop(str(s.cell_value(5, 4)))
    plan_plon = num(s.cell_value(6, 4)); plon = num(s.cell_value(7, 4))
    up = dict(rok=ROK, pole=name, uprawa=c, odm=odm, uwagi=ex, plon=plon if plon else None,
              siew=None, norma=None)
    for r in range(15, s.nrows):
        v = s.row_values(r)
        if not str(v[1]).strip(): continue
        d, draw = date(v[0])
        typ = str(v[5]).strip(); prod = str(v[7]).strip(); zname = str(v[1]).strip()
        val, unit = dose(v[9])
        k = kind(zname, typ)
        notes = [f"eAgronom: {zname}"]
        if draw: notes.append(f"data: {draw}")
        if str(v[16]).strip(): notes.append(str(v[16]).strip())
        if k == "Nawożenie mineralne" and "siew" in zname.lower(): notes.append("nawóz przy siewie")
        if zname == "Siew międzyplonu": notes.append("międzyplon")
        if k == "Uprawa przedsiewna" and not prod: prod = "Kultywator zębowy"
        zabiegi.append(dict(data=d, rok=ROK, pole=name, rodzaj=k, srodek=prod, dawka=val, jedn=unit,
                            pow=num(v[4]), wyk=str(v[3]).strip(), uwagi="; ".join(notes),
                            N=num(v[11]), P=num(v[12]), K=num(v[13]), S=num(v[14]), Mg=num(v[15])))
        if zname != "Siew międzyplonu" and k == "Siew / sadzenie" and up["siew"] is None:
            up["siew"] = d
            if unit == "kg": up["norma"] = val
            elif val: up["uwagi"] = "; ".join(x for x in [up["uwagi"], f"obsada {int(val):,} nasion/ha".replace(",", " ")] if x)
    uprawy.append(up)

json.dump(dict(pola=pola, uprawy=uprawy, zabiegi=zabiegi, season=season), open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
print(len(pola), len(uprawy), len(zabiegi), ROK)
from collections import Counter
print(Counter(z["rodzaj"] for z in zabiegi)); print(Counter(z["jedn"] for z in zabiegi)); print(Counter(u["uprawa"] for u in uprawy))
print([z for z in zabiegi if z["data"] is None])
