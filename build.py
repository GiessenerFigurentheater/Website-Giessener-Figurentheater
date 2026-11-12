#!/usr/bin/env python3
"""Baut die komplette Website aus den Inhalts- und Datendateien.

  content/*.html           Seitentexte (Startseite, Termine, Veranstalter, …)
  inhalte/stuecke/*.json   Repertoire → je Stück eine Unterseite stuecke/<datei>.html
  inhalte/termine.json     Öffentliche Spielserien → Terminlisten, Gastspielseiten, Google-Daten, Kalender
  inhalte/galerie.json     Fotos der Galerie
  assets/                  Stylesheet, Skript, Schrift und Bilder

Die fertige Website entsteht im Ordner _site/. Vergangene Vorstellungen werden automatisch ausgeblendet.
Inhalte werden mit Claude im Chat gepflegt (JSON-Dateien in inhalte/); GitHub baut danach
automatisch neu (.github/workflows/website.yml) – zusätzlich jede Nacht.
Aufruf: python3 build.py
"""
import json, re, html, shutil, subprocess
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
SITE = "https://www.giessener-figurentheater.de"
THEATER = "Gießener Figurentheater"
# Vorschau-Phase: Suchmaschinen sollen den Entwurf noch nicht aufnehmen.
# Beim Live-Gang auf False setzen (dann auch das gelbe Entwurfs-Banner entfernen).
VORSCHAU = True
# Formular-Dienst (Fakturus Formular, EU-Server): Adresse des Formulars aus dem Fakturus-Dashboard, z. B. ".../f/abc123".
# Leer = Anfrage-Formulare öffnen wie bisher das E-Mail-Programm.
FORMULAR_ADRESSE = "https://formular.fakturus.com/f/website-anfragen"
TZ = ZoneInfo("Europe/Berlin")
WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MONATE = ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sep.", "Okt.", "Nov.", "Dez."]
STATUS_SCHEMA = {"geplant": "EventScheduled", "ausverkauft": "EventScheduled",
                 "abgesagt": "EventCancelled", "verschoben": "EventPostponed"}
LOGO = "assets/bilder/logo-giessener-figurentheater.png"
# Feste Fotos der Seiten (früher von der alten IONOS-Seite eingebunden, seit 12.11.2026 in assets/bilder/)
IMG = {
    "BUEHNE": "assets/bilder/buehne-roter-vorhang.jpg",
    "ZELT": "assets/bilder/theaterzelt-sonnenuntergang.jpg",
    "EKZ": "assets/bilder/einkaufscenter-wetzlar.jpg",
    "KINO": "assets/bilder/gastspiel-kinopolis.jpg",
    "CENTER": "assets/bilder/puppenbuehne-einkaufszentrum.jpg",
    "FIGUREN": "assets/bilder/theaterfiguren-gruppe.jpg",
    "KASPER": "assets/bilder/kasper-handpuppe.jpg",
    "WINTER": "assets/bilder/winterliches-buehnenbild.jpg",
    "TEAM": "assets/bilder/patrizia-und-ricardo-sperlich.jpg",
}
e = html.escape

def lies(pfad):
    return json.loads((ROOT / pfad).read_text(encoding="utf-8"))

def slug(text):
    text = text.lower()
    for a, b in (("ß", "ss"), ("ä", "ae"), ("ö", "oe"), ("ü", "ue")):
        text = text.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")

def stueck_slug(wert):
    """Ein Stück wird über seinen Dateinamen erkannt – egal ob als Pfad oder als Name angegeben."""
    return slug(Path(wert or "").stem)

def vervollstaendige(daten, vorlage):
    """Leere oder fehlende Felder mit Standardwerten füllen, leere Listeneinträge entfernen."""
    for k, standard in vorlage.items():
        wert = daten.get(k)
        if wert is None:
            daten[k] = standard
        elif isinstance(standard, list):
            daten[k] = [x for x in wert if x]
        elif isinstance(standard, dict) and isinstance(wert, dict):
            vervollstaendige(wert, standard)
    return daten

STUECK_VORLAGE = {"titel": "", "vorlage": "", "kurz": "", "alter": "", "dauer": "", "zuschauer": "", "spielform": "",
                  "tags": [], "inhalt": [], "highlights": [], "paedagogik": [], "varianten": [], "formate": [], "bilder": [],
                  "presse": {"pressetext": "", "pressefotos": "", "plakat": ""},
                  "zitat": {"text": "", "quelle": ""}, "mitwirkende": [], "premiere": ""}
SERIE_VORLAGE = {"titel": "", "beschreibung": "", "ort": {"name": "", "strasse": "", "plz": "", "stadt": ""},
                 "zeiten": {t: "" for t in WOCHENTAGE}, "ausfall": [], "zusatz": [],
                 "preise": [], "bild": "", "status": "geplant", "vorverkauf": {"text": "", "link": ""}}

stuecke = []
for datei in sorted((ROOT / "inhalte" / "stuecke").glob("*.json")):
    st = vervollstaendige(lies(datei.relative_to(ROOT)), STUECK_VORLAGE)
    st["bilder"] = [b for b in st["bilder"] if b.get("src")]
    if st.get("sichtbar", True) and st["titel"]:
        stuecke.append({**st, "slug": stueck_slug(datei.name)})
def mit_ca(dauer):
    """Spieldauer immer als Circa-Angabe – live gespielt, die Zeit variiert. Offene [Platzhalter] bleiben unverändert."""
    d = (dauer or "").strip()
    if not d or d.startswith("[") or d.lower().startswith("ca"):
        return d
    return "ca. " + d

def dauer_minuten(dauer, standard=60):
    """Längste Zahl aus der Dauer-Angabe des Stücks, z. B. „ca. 30–45 Minuten“ → 45 (für Kalender-Endzeiten)."""
    zahlen = [int(z) for z in re.findall(r"\d+", dauer or "")]
    return max(zahlen) if zahlen else standard

for st in stuecke:
    st["dauer"] = mit_ca(st["dauer"])
stuecke.sort(key=lambda st: (st.get("reihenfolge") or 999, st["titel"]))
STUECK = {st["slug"]: st for st in stuecke}
termin_daten = lies("inhalte/termine.json")
galerie = [g for g in lies("inhalte/galerie.json") if g.get("bild")]
# Nur freigegebene 5-Sterne-Bewertungen werden gezeigt
bewertungen = [b for b in lies("inhalte/bewertungen.json")
               if b.get("anzeigen", True) and int(b.get("sterne") or 0) == 5 and (b.get("text") or "").strip()]
google = lies("inhalte/google.json")
kulturzelt = lies("inhalte/kulturzelt.json")
site, theater = SITE, THEATER
now = datetime.now(TZ)

# ---------- Bilder ----------
def lokal(src):
    """Bildpfade in den Inhalten beginnen mit „/“ – für die Website relativ machen."""
    return src.lstrip("/") if src and not src.startswith("http") else src

def verkleinern(quelle, ziel, breite=1000):
    """Kleine Bildversion fürs Handy: mit Pillow (auf GitHub) oder sips (Mac); sonst Original kopieren."""
    ziel.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageOps
        with Image.open(quelle) as bild:
            bild = ImageOps.exif_transpose(bild).convert("RGB")
            bild.thumbnail((breite, breite * 2))
            bild.save(ziel, "JPEG", quality=78, optimize=True, progressive=True)
        return
    except ImportError:
        pass
    if shutil.which("sips"):
        r = subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "78", "-Z", str(breite), str(quelle), "--out", str(ziel)],
                           capture_output=True)
        if r.returncode == 0:
            return
    shutil.copyfile(quelle, ziel)

def klein_pfad(src):
    src = lokal(src)
    if src.startswith("http") or not src.startswith("assets/bilder/"):
        return src
    return "assets/bilder/klein/" + Path(src).with_suffix(".jpg").name


def todo(text):
    """[eckige Klammern] in Texten als offene Angabe gelb markieren."""
    return re.sub(r"\[([^\]]+)\]", r'<mark class="todo">\1</mark>', e(text))


# ---------- Termine ----------
def zeiten_am(s, tag):
    """Uhrzeiten eines Wochentags als Liste, z. B. ["11:00", "14:00"]. Toleriert „15.00“ und Semikolons."""
    text = (s["zeiten"].get(tag) or "").replace(";", ",").replace(".", ":")
    return [z.strip() for z in text.split(",") if z.strip()]

def vorstellungen(s):
    """Alle kommenden Einzelvorstellungen einer Serie als (start, ende)."""
    starts = []
    d, bis = date.fromisoformat(s["von"][:10]), date.fromisoformat(s["bis"][:10])
    ausfall = {a[:10] for a in s.get("ausfall") or []}
    while d <= bis:
        if d.isoformat() not in ausfall:
            for zeit in zeiten_am(s, WOCHENTAGE[d.weekday()]):
                h, m = map(int, zeit.split(":"))
                starts.append(datetime(d.year, d.month, d.day, h, m, tzinfo=TZ))
        d += timedelta(days=1)
    starts += [datetime.fromisoformat(z[:16]).replace(tzinfo=TZ) for z in s.get("zusatz") or [] if z]
    dauer = timedelta(minutes=s["dauer_min"])
    return sorted((st, st + dauer) for st in starts if st + dauer >= now)

serien = []
for s in termin_daten:
    vervollstaendige(s, SERIE_VORLAGE)
    if not (s.get("von") and s.get("bis") and s["titel"]):
        continue
    s["stueck"] = stueck_slug(s.get("stueck"))
    s["preise"] = [{"name": p.get("name") or "Eintritt", "preis": str(p["preis"]).replace("€", "").strip()}
                   for p in s["preise"] if p.get("preis")]
    # Spieldauer kommt immer vom Stück (für Endzeiten in Kalender & Google-Daten)
    s["dauer_min"] = dauer_minuten(STUECK.get(s["stueck"], {}).get("dauer"))
    s["_id"] = f'{s["stueck"]}-{slug(s["ort"]["stadt"])}-{s["von"]}'
    s["_shows"] = vorstellungen(s)
    if s["_shows"]:
        serien.append(s)
serien.sort(key=lambda s: s["_shows"][0][0])

def adresse(o):
    teile = [o["name"], o.get("strasse"), " ".join(x for x in (o.get("plz"), o["stadt"]) if x)]
    return ", ".join(t for t in teile if t)

def utc(d):
    return d.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def kurzdatum(d):
    return f"{d.day}. {MONATE[d.month-1]}"

def google_link(s, start, end):
    q = {"action": "TEMPLATE", "text": f'{s["titel"]} – {theater}',
         "dates": f"{utc(start)}/{utc(end)}",
         "details": f'{s["beschreibung"]}\n{"Vorverkauf: " + (vorverkauf(s)[1] or vorverkauf(s)[0]) + chr(10) if any(vorverkauf(s)) else ""}Tickets an der Kasse 30 Min. vor Beginn.\nAlle Infos: {site}/{gastspiel_url(s)}', "location": adresse(s["ort"])}
    return "https://calendar.google.com/calendar/render?" + urlencode(q)

def vorverkauf(s):
    """Optionaler Vorverkauf einer Spielserie: (Hinweistext, Ticket-Link) – beides darf leer sein."""
    v = s.get("vorverkauf") or {}
    return (v.get("text") or "").strip(), (v.get("link") or "").strip()

def gastspiel_url(s):
    """Jede Spielserie hat eine eigene Seite: gastspiele/<stück>-<stadt>-<startdatum>.html"""
    return f'gastspiele/{s["_id"]}.html'

def termin_bild(s):
    """Bild einer Spielserie: eigenes Bild beim Termin, sonst Titelbild des Stücks."""
    if s.get("bild"):
        return {"src": s["bild"], "alt": f'Szene aus {s["titel"]}'}
    st = STUECK.get(s["stueck"])
    return st["bilder"][0] if st and st["bilder"] else None

def termin_media(s, root, first):
    b = termin_bild(s)
    bild = (f'<img src="{e(bild_src(b, root, True))}" alt="{e(b["alt"])}" loading="lazy"{fokus(b)}>' if b
            else f'<div class="ph">Foto folgt<br>{e(s["titel"])}</div>')
    ziel = root + gastspiel_url(s)
    return (f'<a class="ev-media" href="{ziel}" tabindex="-1" aria-hidden="true">{bild}'
            f'<span class="ev-date"><span>ab</span><strong>{first.day}</strong><span>{MONATE[first.month-1]}</span></span></a>')

ICON_KALENDER = ('<svg class="ev-icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3"/>'
                 '<path d="M3 10h18M8 3v4M16 3v4"/></svg>')
ICON_ORT = ('<svg class="ev-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/>'
            '<circle cx="12" cy="9.5" r="2.5"/></svg>')

def termin_karte(s, root, compact=False):
    o, shows = s["ort"], s["_shows"]
    first, last = shows[0][0], shows[-1][0]
    zeitraum = f"{kurzdatum(first)} {first.year}" if first.date() == last.date() else f"{kurzdatum(first)} – {kurzdatum(last)} {last.year}"
    anzahl = "1 Aufführung" if len(shows) == 1 else f"{len(shows)} Aufführungen"
    ort_zeile = ", ".join(x for x in (o["name"], o.get("strasse")) if x)
    badge = {"ausverkauft": " <span class=\"ev-badge\">Ausverkauft</span>",
             "abgesagt": " <span class=\"ev-badge\">Abgesagt</span>",
             "verschoben": " <span class=\"ev-badge\">Verschoben</span>"}.get(s["status"], "")
    preise = " · ".join(f'{e(p["name"])} {e(p["preis"])} €' for p in s["preise"])
    titel = f'<a href="{root}{gastspiel_url(s)}">{e(s["titel"])}</a>'
    return f'''<article class="ev{' compact' if compact else ''}" id="termin-{s["_id"]}">
      {f'<div class="ev-date"><span>ab</span><strong>{first.day}</strong><span>{MONATE[first.month-1]}</span></div>' if compact else termin_media(s, root, first)}
      <div>
        <h3>{titel}{badge}</h3>
        <div class="ev-key">
          <div class="ev-key-item">{ICON_KALENDER}<span><small>Wann</small><b>{zeitraum}</b></span></div>
          <div class="ev-key-item">{ICON_ORT}<span><small>Wo</small><b>{e(o["stadt"])}</b><em>{e(ort_zeile)}</em></span></div>
        </div>
        <p class="ev-meta">{anzahl}{' · <span class="vvk-tag">Vorverkauf</span>' if any(vorverkauf(s)) else ""}{"" if compact else " · Eintritt: " + preise}</p>
      </div>
      <div class="ev-actions">
        <a class="btn" href="{root}{gastspiel_url(s)}">Details & Tickets</a>
        <a class="btn ghost" href="{root}kalender/{s["_id"]}.ics">In Kalender</a>
      </div>
    </article>'''

def termin_liste(liste, root, compact=False, leer="Aktuell sind keine öffentlichen Vorstellungen geplant."):
    if not liste:
        return f'<p class="empty">{leer}</p>'
    return '<div class="events">\n    ' + "\n    ".join(termin_karte(s, root, compact) for s in liste) + "\n  </div>"

# ---------- Schema.org ----------
ORG = {"@type": "PerformingGroup", "@id": f"{site}/#theater", "name": theater, "url": site + "/",
       "logo": f"{site}/{LOGO}", "email": "info@giessener-figurentheater.de", "telephone": "+49 160 4625287",
       "address": {"@type": "PostalAddress", "streetAddress": "Bachstraße 42", "postalCode": "35435",
                   "addressLocality": "Wettenberg", "addressCountry": "DE"},
       "sameAs": ["https://www.instagram.com/giessenerfigurentheater/", "https://www.facebook.com/figurentheater.giessen/"]}

def bild_absolut(b):
    """Google braucht vollständige Bildadressen; ohne Stückfoto wird das Theaterzelt gezeigt."""
    if not b:
        return f'{site}/{IMG["ZELT"]}'
    return b["src"] if b["src"].startswith("http") else f'{site}/{lokal(b["src"])}'

def events_jsonld(liste):
    out = []
    for s in liste:
        o = s["ort"]
        for start, end in s["_shows"]:
            out.append({
                "@type": "TheaterEvent",
                "@id": f'{site}/{gastspiel_url(s)}#vorstellung-{start:%Y%m%d-%H%M}',
                "name": f'{s["titel"]} – Puppentheater in {o["stadt"]}',
                "description": s["beschreibung"],
                "startDate": start.isoformat(), "endDate": end.isoformat(),
                "eventStatus": f'https://schema.org/{STATUS_SCHEMA[s["status"]]}',
                "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                "inLanguage": "de", "isAccessibleForFree": False,
                "image": [bild_absolut(termin_bild(s))],
                "url": f'{site}/{gastspiel_url(s)}',
                "location": {"@type": "Place", "name": o["name"], "address": {
                    "@type": "PostalAddress", "streetAddress": o.get("strasse", ""), "postalCode": o.get("plz", ""),
                    "addressLocality": o["stadt"], "addressCountry": "DE"}},
                "organizer": {"@id": ORG["@id"]}, "performer": {"@id": ORG["@id"]},
                "offers": [{"@type": "Offer", "name": p["name"], "price": f'{preis_zahl(p["preis"]):.2f}',
                            "priceCurrency": "EUR", "url": vorverkauf(s)[1] or f"{site}/{gastspiel_url(s)}#tickets",
                            "availability": "https://schema.org/SoldOut" if s["status"] == "ausverkauft" else "https://schema.org/InStock"}
                           for p in s["preise"]],
            })
    return out

def jsonld(*nodes):
    data = json.dumps({"@context": "https://schema.org", "@graph": [ORG, *nodes]}, ensure_ascii=False, indent=1)
    return '<script type="application/ld+json">\n' + data.replace("</", "<\\/") + "\n</script>"

# ---------- Kalender ----------
def ics_escape(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def ics_fold(line):
    out, cur = [], ""
    for ch in line:
        if len((cur + ch).encode()) > 74:
            out.append(cur); cur = " " + ch
        else:
            cur += ch
    return "\r\n".join(out + [cur])

def calendar(liste, name):
    host = re.sub(r"^https?://", "", site)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{theater}//Termine//DE", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", f"X-WR-CALNAME:{ics_escape(name)}", "X-WR-TIMEZONE:Europe/Berlin",
             "REFRESH-INTERVAL;VALUE=DURATION:PT12H"]
    for s in liste:
        preise = " · ".join(f'{p["name"]} {p["preis"]} €' for p in s["preise"])
        for start, end in s["_shows"]:
            lines += ["BEGIN:VEVENT", f'UID:{s["_id"]}-{start:%Y%m%d%H%M}@{host}', f"DTSTAMP:{utc(now)}",
                      f"DTSTART:{utc(start)}", f"DTEND:{utc(end)}",
                      f'SUMMARY:{ics_escape(s["titel"] + " – " + theater)}',
                      f'DESCRIPTION:{ics_escape(s["beschreibung"] + chr(10) + "Eintritt: " + preise + chr(10) + ("Vorverkauf: " + (vorverkauf(s)[1] or vorverkauf(s)[0]) + chr(10) if any(vorverkauf(s)) else "") + "Tickets an der Kasse 30 Min. vor Beginn (nur Barzahlung).")}',
                      f'LOCATION:{ics_escape(adresse(s["ort"]))}', f'URL:{site}/{gastspiel_url(s)}',
                      "STATUS:" + ("CANCELLED" if s["status"] == "abgesagt" else "CONFIRMED"), "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(ics_fold(l) for l in lines) + "\r\n"

# ---------- Bausteine Stücke ----------
FOKUS = {"oben": "center top", "mitte": "center", "unten": "center bottom"}

def fokus(b):
    """Bildausschnitt für hochkante Fotos (oben/mitte/unten), damit z. B. Köpfe nicht abgeschnitten werden."""
    pos = FOKUS.get((b or {}).get("fokus") or "mitte", "center")
    return "" if pos == "center" else f' style="object-position:{pos}"'

def bild_src(b, root, klein=False):
    """Eigene Bilder liegen in assets/bilder/ – Pfad passend zur Seite ergänzen, fürs Handy die kleine Version."""
    src = klein_pfad(b["src"]) if klein else lokal(b["src"])
    return src if src.startswith("http") else root + src

def bild_oder_platzhalter(st, root, label="Foto folgt", klein=True):
    if st["bilder"]:
        b = st["bilder"][0]
        return f'<img src="{e(bild_src(b, root, klein))}" alt="{e(b["alt"])}" loading="lazy"{fokus(b)}>'
    return f'<div class="ph">{label}<br>{e(st["titel"])}</div>'

def kurz_html(st):
    """Kurzbeschreibung für Karten: ein Zitat (z. B. der erste Satz aus dem Buch) steht kursiv davor."""
    z = (st["zitat"].get("text") or "").strip()
    return (f'<i>„{e(z)}“</i> – ' if z else "") + todo(st["kurz"])

def kurz_text(st):
    """Dasselbe als reiner Text, z. B. für die Google-Beschreibung."""
    z = (st["zitat"].get("text") or "").strip()
    return (f"„{z}“ – " if z else "") + st["kurz"]

def zitat_block(st):
    """Zitat mit Quellenangabe oben auf der Stückseite."""
    z = (st["zitat"].get("text") or "").strip()
    if not z:
        return ""
    q = (st["zitat"].get("quelle") or "").strip()
    return (f'<blockquote class="person-quote stueck-zitat">„{e(z)}“'
            + (f'<cite>{e(q)}</cite>' if q else "") + "</blockquote>")

def mitwirkende_html(st):
    """Team der Inszenierung (Spiel, Text, Figuren, Bühnenbild …) und Uraufführung als kleine Liste."""
    zeilen = [(m.get("rolle", ""), m.get("name", "")) for m in st["mitwirkende"] if m.get("name")]
    if st["premiere"]:
        zeilen.append(("Uraufführung", st["premiere"]))
    if not zeilen:
        return ""
    return ('<h3 style="margin-top:36px">Mitwirkende</h3><dl class="steckbrief mitwirkende">'
            + "".join(f"<dt>{e(r)}</dt><dd>{todo(n)}</dd>" for r, n in zeilen) + "</dl>")

def stueck_karten(root, liste=None, css="plays"):
    return f'<div class="{css}">\n' + "\n".join(f'''    <a class="play" href="{root}stuecke/{st["slug"]}.html">
      {bild_oder_platzhalter(st, root)}
      <div class="play-body">
        <div class="tags">{"".join(f'<span class="tag">{e(t)}</span>' for t in st["tags"])}</div>
        <h3>{e(st["titel"])}</h3>
        <p>{kurz_html(st)}</p>
        <p><b>{todo(st["alter"])}</b> · {todo(st["dauer"])}</p>
      </div>
    </a>''' for st in (stuecke if liste is None else liste)) + "\n  </div>"

def stueck_tabelle(root):
    rows = "\n".join(f'''      <tr><td><a href="{root}stuecke/{st["slug"]}.html"><b>{e(st["titel"])}</b></a>{"".join(f"<br><small>+ {e(v['titel'])}</small>" for v in st["varianten"])}</td>
        <td>{todo(st["alter"])}</td><td>{todo(st["dauer"])}</td><td>{todo(st["zuschauer"])}</td><td>{todo(", ".join(st["formate"]))}</td></tr>''' for st in stuecke)
    return f'''<div class="table-wrap"><table>
      <thead><tr><th>Stück</th><th>Alter</th><th>Dauer</th><th>Zuschauer</th><th>Formate</th></tr></thead>
      <tbody>
{rows}
      </tbody></table></div>'''

def stueck_optionen():
    opts = ['<option value="Noch unentschlossen – bitte beraten">Noch unentschlossen – bitte beraten</option>']
    for st in stuecke:
        opts.append(f'<option data-slug="{st["slug"]}">{e(st["titel"])}</option>')
        opts += [f'<option data-slug="{st["slug"]}">{e(v["titel"])}</option>' for v in st["varianten"]]
    return "\n          ".join(opts)

PRESSE_DATEIEN = [("pressetext", "Pressetext"), ("pressefotos", "Pressefotos"), ("plakat", "Plakatmotiv")]

def datei_info(src):
    """Dateityp und -größe für die Download-Liste, z. B. „PDF · 1,2 MB“."""
    endung = Path(src).suffix.lstrip(".").upper() or "Datei"
    pfad = ROOT / lokal(src)
    if src.startswith("http") or not pfad.exists():
        return endung
    mb = pfad.stat().st_size / 1_000_000
    groesse = f"{mb:.1f} MB".replace(".", ",") if mb >= 0.1 else f"{max(1, round(mb * 1000))} KB"
    return f"{endung} · {groesse}"

def presse_box(st, root):
    """Downloads für Presse & Veranstalter; fehlende Dateien erscheinen als „folgt in Kürze“."""
    zeilen = []
    for feld, label in PRESSE_DATEIEN:
        src = (st["presse"].get(feld) or "").strip()
        if src:
            href = src if src.startswith("http") else root + lokal(src)
            zeilen.append(f'<li><a class="dl" href="{e(href)}" download><span class="dl-icon" aria-hidden="true">↓</span>'
                          f'<span><b>{label}</b><small>{e(datei_info(src))}</small></span></a></li>')
        else:
            zeilen.append(f'<li><span class="dl dl-leer"><span class="dl-icon" aria-hidden="true">↓</span>'
                          f'<span><b>{label}</b><small>folgt in Kürze</small></span></span></li>')
    fehlt = any(not (st["presse"].get(f) or "").strip() for f, _ in PRESSE_DATEIEN)
    hinweis = ('<p class="dl-hinweis">Material fehlt? Schreibt uns an '
               '<a href="mailto:info@giessener-figurentheater.de">info@giessener-figurentheater.de</a>.</p>') if fehlt else ""
    return f'''<aside class="box presse">
      <h3>Presse &amp; Material</h3>
      <p>Für Programmhefte, Plakate und die Presse – zum Herunterladen.</p>
      <ul class="downloads-liste">{"".join(zeilen)}</ul>
      {hinweis}
    </aside>'''

def stueck_seite(st):
    root = "../"
    eigene = [s for s in serien if s["stueck"] == st["slug"]]
    andere = [x for x in stuecke if x["slug"] != st["slug"]]
    galerie = ("\n".join(f'<figure><img src="{e(bild_src(b, root, True))}" alt="{e(b["alt"])}" loading="lazy"{fokus(b)}><figcaption>{e(b.get("text", ""))}</figcaption></figure>' for b in st["bilder"])
               or "\n".join(f'<div class="ph">{t}<br>folgt</div>' for t in ("Szenenfoto", "Figuren", "Bühnenbild")))
    varianten = "".join(f'<div class="box"><h3>{e(v["titel"])}</h3><p>{todo(v["text"])}</p></div>' for v in st["varianten"])
    body = f'''
<div class="wrap breadcrumb"><a href="{root}index.html">Start</a> › <a href="{root}stuecke/index.html">Repertoire</a> › {e(st["titel"])}</div>

<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <div class="tags">{"".join(f'<span class="tag">{e(t)}</span>' for t in st["tags"])}</div>
      <h1 style="margin-top:.4em">{e(st["titel"])}</h1>
      <p class="lead">{todo(st["vorlage"])}</p>
      {zitat_block(st)}
      <p class="lead">{todo(st["kurz"])}</p>
      <div class="btns"><a class="btn" href="{root}veranstalter.html?stueck={st["slug"]}#anfrage">Stück anfragen</a>
      <a class="btn ghost" href="#termine">Öffentliche Termine</a></div>
    </div>
    <div class="hero-media">{bild_oder_platzhalter(st, root, "Titelfoto folgt", klein=False)}</div>
  </div>
  <div class="wrap">
    <ul class="facts" style="margin-top:56px">
      <li><small>Alter</small><b>{todo(st["alter"])}</b></li>
      <li><small>Dauer</small><b>{todo(st["dauer"])}</b></li>
      <li><small>Zuschauer</small><b>{todo(st["zuschauer"])}</b></li>
      <li><small>Spielform</small><b>{todo(st["spielform"])}</b></li>
    </ul>
  </div>
</section>

<section class="alt">
  <div class="wrap">
    <span class="eyebrow">Bilder</span><h2>Einblicke ins Stück</h2>
    <div class="gallery">
      {galerie}
    </div>
  </div>
</section>

<section>
  <div class="wrap split">
    <div>
      <span class="eyebrow">Inhalt</span>
      <h2>Darum geht's</h2>
      {"".join(f'<p class="lead">{todo(p)}</p>' for p in st["inhalt"])}
      <h3 style="margin-top:36px">Das erwartet die Kinder</h3>
      <ul class="checklist">{"".join(f"<li>{todo(h)}</li>" for h in st["highlights"])}</ul>
      <h3 style="margin-top:36px">Pädagogischer Wert</h3>
      <ul class="checklist">{"".join(f"<li>{todo(p)}</li>" for p in st["paedagogik"])}</ul>
      {mitwirkende_html(st)}
    </div>
    <div class="sticky-box">
    <aside class="box">
      <span class="section-label">FÜR VERANSTALTER</span>
      <h3>Dieses Stück buchen</h3>
      <p>Spielbar als: {todo(", ".join(st["formate"]))}</p>
      <p>Platzbedarf und Technik findet ihr auf der Veranstalterseite.</p>
      <div class="btns"><a class="btn" href="{root}veranstalter.html?stueck={st["slug"]}#anfrage">Stück anfragen</a>
      <a class="btn ghost" href="{root}veranstalter.html">Alle Infos</a></div>
    </aside>
    {presse_box(st, root)}
    </div>
  </div>
</section>
{f"""
<section class="alt">
  <div class="wrap">
    <span class="section-label">VARIANTEN</span>
    <span class="eyebrow">Varianten</span><h2>Auch als …</h2>
    <div class="grid">{varianten}</div>
  </div>
</section>""" if varianten else ""}

<section id="termine">
  <div class="wrap">
    <span class="eyebrow">Termine</span>
    <h2>Öffentliche Vorstellungen</h2>
    {termin_liste(eigene, root, leer="Zurzeit keine öffentlichen Termine – aber ihr könnt das Stück für eure Einrichtung oder Veranstaltung buchen.")}
    <a class="more" href="{root}termine.html">Alle Termine →</a>
  </div>
</section>

<section class="alt">
  <div class="wrap">
    <span class="section-label">WEITERE STÜCKE</span>
    <span class="eyebrow">Repertoire</span><h2>Das könnte auch gefallen</h2>
    <div class="plays">{"".join(f'<a class="play" href="{x["slug"]}.html">{bild_oder_platzhalter(x, root)}<div class="play-body"><h3>{e(x["titel"])}</h3><p>{kurz_html(x)}</p></div></a>' for x in andere)}</div>
  </div>
</section>'''
    return body, eigene

# ---------- Gastspielseiten ----------
def maps_link(o):
    return "https://www.google.com/maps/search/?" + urlencode({"api": 1, "query": adresse(o)})

def preis_zahl(text):
    treffer = re.search(r"\d+(?:[.,]\d+)?", text)
    return float(treffer[0].replace(",", ".")) if treffer else 0.0

def gastspiel_seite(s):
    root = "../"
    o, shows = s["ort"], s["_shows"]
    st = STUECK.get(s["stueck"])
    first, last = shows[0][0], shows[-1][0]
    zeitraum = f"{kurzdatum(first)} {first.year}" if first.date() == last.date() else f"{kurzdatum(first)} – {kurzdatum(last)} {last.year}"
    b = termin_bild(s)
    bild = (f'<img src="{e(bild_src(b, root))}" alt="{e(b["alt"])}"{fokus(b)}>' if b
            else f'<div class="ph">Foto folgt<br>{e(s["titel"])}</div>')
    ab_preis = min((p["preis"] for p in s["preise"]), key=preis_zahl, default="–")
    badge = {"ausverkauft": "Ausverkauft", "abgesagt": "Abgesagt", "verschoben": "Verschoben"}.get(s["status"])

    tage = {}
    for start, end in shows:
        tage.setdefault(start.date(), []).append((start, end))
    zeilen = []
    for d, z in tage.items():
        zeiten = " · ".join(f'<time datetime="{a.isoformat()}" id="vorstellung-{a:%Y%m%d-%H%M}">{a:%H:%M} Uhr</time>' for a, _ in z)
        links = " ".join(
            f'<a href="{e(google_link(s, a, en))}" target="_blank" rel="noopener">+ Google Kalender{f" ({a:%H:%M})" if len(z) > 1 else ""}</a>'
            for a, en in z)
        zeilen.append(f"        <tr><td><b>{WOCHENTAGE[d.weekday()]}, {kurzdatum(d)}</b></td><td>{zeiten}</td><td>{links}</td></tr>")
    zeilen = "\n".join(zeilen)

    preise = "".join(f'<li><span>{e(p["name"])}</span> <b>{e(p["preis"])} €</b></li>' for p in s["preise"])
    andere = [x for x in serien if x is not s]
    badge_html = f'<p><span class="ev-badge">{badge}</span></p>' if badge else ""
    strasse_fehlt = "" if o.get("strasse") else '<p><mark class="todo">Straße & PLZ ergänzen – hilft Google und Navigationsgeräten</mark></p>'

    vvk_text, vvk_link = vorverkauf(s)
    vvk_html = ""
    if vvk_text or vvk_link:
        vvk_html = (f'<div class="vvk"><b>Tickets im Vorverkauf</b>'
                    f'<p>{e(vvk_text or "Für dieses Gastspiel gibt es einen Vorverkauf.")}</p>'
                    + (f'<a class="btn" href="{e(vvk_link)}" target="_blank" rel="noopener">Zum Vorverkauf</a>' if vvk_link else "")
                    + '</div>')
    stueck_box = ""
    if st:
        stueck_box = f"""
<section class="alt">
  <div class="wrap split center">
    <div>
      <span class="eyebrow">Über das Stück</span>
      <h2>{e(st["titel"])}</h2>
      <p class="lead">{todo(st["vorlage"])}</p>
      <p class="lead">{kurz_html(st)}</p>
      <ul class="facts" style="margin-top:20px">
        <li><small>Alter</small><b>{todo(st["alter"])}</b></li>
        <li><small>Dauer</small><b>{todo(st["dauer"])}</b></li>
      </ul>
      <div class="btns"><a class="btn ghost" href="{root}stuecke/{st["slug"]}.html">Mehr zum Stück</a></div>
    </div>
    <div class="hero-media">{bild_oder_platzhalter(st, root)}</div>
  </div>
</section>"""

    body = f"""
<div class="wrap breadcrumb"><a href="{root}index.html">Start</a> › <a href="{root}termine.html">Termine</a> › {e(s["titel"])} in {e(o["stadt"])}</div>

<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <span class="eyebrow">Puppentheater in {e(o["stadt"])}</span>
      <h1>{e(s["titel"])} <span class="hl">in {e(o["stadt"])}</span></h1>
      {badge_html}
      <p class="lead">{e(s["beschreibung"])}</p>
      <div class="btns">
        <a class="btn" href="#vorstellungen">Alle {len(shows)} Vorstellungen</a>
        <a class="btn ghost" href="{root}kalender/{s["_id"]}.ics">In Kalender eintragen</a>
      </div>
    </div>
    <div class="hero-media">{bild}</div>
  </div>
  <div class="wrap">
    <ul class="facts" style="margin-top:56px">
      <li><small>Zeitraum</small><b>{zeitraum}</b></li>
      <li><small>Spielort</small><b>{e(o["name"])}</b></li>
      <li><small>Eintritt</small><b>ab {e(ab_preis)} €</b></li>
      <li><small>Tickets</small><b>{"Vorverkauf & Kasse vor Ort" if any(vorverkauf(s)) else "an der Kasse vor Ort"}</b></li>
    </ul>
  </div>
</section>

<section class="alt" id="vorstellungen">
  <div class="wrap">
    <span class="eyebrow">Spielzeiten</span>
    <h2>Alle Vorstellungen</h2>
    <p class="lead">Einlass und Kassenöffnung jeweils 30 Minuten vor Beginn.</p>
    <div class="table-wrap"><table>
      <thead><tr><th>Tag</th><th>Uhrzeit</th><th>Kalender</th></tr></thead>
      <tbody>
{zeilen}
      </tbody></table></div>
  </div>
</section>

<section id="tickets">
  <div class="wrap grid two" style="margin-top:0">
    <div class="box">
      <span class="eyebrow">Tickets & Eintritt</span>
      <h2>Eintritt</h2>
      <ul class="checklist">{preise}</ul>
      {vvk_html}
      <p style="margin-top:14px">{"Außerdem gibt es" if any(vorverkauf(s)) else "Tickets gibt es"} {"Tickets " if any(vorverkauf(s)) else ""}30 Minuten vor Beginn an der Kasse – <b>nur Barzahlung</b>, freie Platzwahl. Kinder unter 2 Jahren frei (ohne eigenen Sitzplatz). Bei „B“ oder „H“ im Ausweis ist eine Begleitperson frei.</p>
      <p style="margin-top:10px">Gruppen ab 10 Personen: Plätze reservieren unter <a href="tel:+491604625287">0160 / 46 25 287</a>.</p>
    </div>
    <div class="box" id="spielort">
      <span class="eyebrow">Spielort</span>
      <h2>{e(o["name"])}</h2>
      <p class="lead">{e(adresse(o))}</p>
      {strasse_fehlt}
      <div class="btns"><a class="btn" href="{e(maps_link(o))}" target="_blank" rel="noopener">Route planen</a></div>
    </div>
  </div>
</section>
{stueck_box}

<section>
  <div class="wrap">
    <span class="eyebrow">Weitere Termine</span>
    <h2>Auch auf dem Spielplan</h2>
    {termin_liste(andere, root, leer="Weitere Gastspiele folgen bald.")}
    <a class="more" href="{root}termine.html">Alle Termine →</a>
  </div>
</section>"""
    titel = f'{s["titel"]} in {o["stadt"]} – {zeitraum} | Puppentheater'
    desc = (f'{s["titel"]} – Puppentheater für Kinder in {o["stadt"]}, {o["name"]}. '
            f'{zeitraum}, {len(shows)} Vorstellungen. Eintritt ab {ab_preis} €, Tickets {"im Vorverkauf und " if any(vorverkauf(s)) else ""}an der Kasse.')
    return titel, desc, body, bild_absolut(b)

# ---------- Seitenrahmen ----------
# Versions-Stempel: ändert sich mit dem Inhalt, damit Browser nach Änderungen sofort die neue Datei laden
import hashlib
VERSION = {n: hashlib.md5((ROOT / "assets" / n).read_bytes()).hexdigest()[:8] for n in ("style.css", "site.js")}

NAV = [("index.html", "Start"), ("termine.html", "Termine & Tickets"), ("stuecke/index.html", "Repertoire"),
       ("galerie.html", "Galerie"), ("ueber-uns.html", "Über uns"), ("kulturzelt.html", "KULTURzelt"),
       ("veranstalter.html", "Für Veranstalter")]

def layout(path, title, description, body, ld, bild=None):
    root = "../" * path.count("/")
    def aktiv(href):
        gleich = (href == path or (href.startswith("stuecke/") and path.startswith("stuecke/"))
                  or (href == "termine.html" and path.startswith("gastspiele/")))
        return ' aria-current="page"' if gleich else ""
    nav = "\n      ".join(f'<li><a href="{root}{href}"{aktiv(href)}>{label}</a></li>' for href, label in NAV)
    return f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">{'<meta name="robots" content="noindex, nofollow">' if VORSCHAU else ""}
<script>document.documentElement.classList.add("js")</script>
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{site}/{path if path != "index.html" else ""}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="website">
<meta property="og:image" content="{e(bild or site + "/" + IMG["ZELT"])}">
<link rel="alternate" type="text/calendar" title="Termine (iCal)" href="{root}termine.ics">
<link rel="preload" href="{root}assets/fonts/plus-jakarta-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{root}assets/style.css?v={VERSION["style.css"]}">
{ld}
</head>
<body{f' data-formular="{e(FORMULAR_ADRESSE)}"' if FORMULAR_ADRESSE else ""}>
<div class="placeholder-banner">Entwurf – <mark class="todo">gelb markiert</mark> = Angabe fehlt noch oder ist ein Textvorschlag.</div>
<header class="top">
  <div class="wrap nav">
    <a class="logo" href="{root}index.html"><img src="{root}{LOGO}" alt="{e(theater)}" width="148" height="46"></a>
    <button class="menu-btn" aria-label="Menü öffnen">☰</button>
    <ul id="menu">
      {nav}
    </ul>
    <a class="btn" href="{root}veranstalter.html#anfrage">Vorstellung buchen</a>
  </div>
</header>
<main>
{body}
</main>
<footer class="site">
  <div class="wrap">
    <div><b>{e(theater)}</b><br>Patrizia & Ricardo Sperlich<br>Bachstraße 42 · 35435 Wettenberg<br>
      <a href="tel:+491604625287">0160 / 46 25 287</a><br><a href="mailto:info@giessener-figurentheater.de">info@giessener-figurentheater.de</a></div>
    <div><b>Für Familien</b><ul><li><a href="{root}termine.html">Termine</a></li><li><a href="{root}termine.html#tickets">Tickets & Eintritt</a></li><li><a href="{root}termine.ics">Kalender abonnieren</a></li></ul></div>
    <div><b>Für Veranstalter</b><ul><li><a href="{root}veranstalter.html">Infos & Technik</a></li><li><a href="{root}stuecke/index.html">Repertoire</a></li><li><a href="{root}veranstalter.html#anfrage">Buchungsanfrage</a></li><li><a href="{root}kulturzelt.html">KULTURzelt mieten</a></li></ul></div>
    <div><b>Folgt uns</b><ul><li><a href="https://www.instagram.com/giessenerfigurentheater/">Instagram</a></li><li><a href="https://www.facebook.com/figurentheater.giessen/">Facebook</a></li><li><a href="{root}ueber-uns.html">Über uns</a></li><li><a href="{root}galerie.html">Galerie</a></li><li><a href="{root}impressum.html">Impressum</a> · <a href="{root}datenschutz.html">Datenschutz</a></li></ul></div>
  </div>
</footer>
<script src="{root}assets/site.js?v={VERSION["site.js"]}"></script>
</body>
</html>
'''

def naechster_termin_bild(root):
    """Großes Bild oben auf „Termine & Tickets“: immer das Bild der nächsten Vorstellung (sonst das Theaterzelt)."""
    b = termin_bild(serien[0]) if serien else None
    if not b:
        return f'<img src="{e(root + IMG["ZELT"])}" alt="Das Theaterzelt des Gießener Figurentheaters bei Sonnenuntergang">'
    return f'<img src="{e(bild_src(b, root))}" alt="{e(b["alt"])}"{fokus(b)}>'

def naechster_termin_badge(root):
    if not serien:
        return ""
    s = serien[0]
    st = s["_shows"][0][0]
    return (f'<a class="float" href="{root}{gastspiel_url(s)}" style="text-decoration:none;color:inherit">'
            f'<span class="dot">{st.day}.</span><span><small>Nächste Vorstellung · {e(s["ort"]["stadt"])}</small>'
            f'<strong>{e(s["titel"])}</strong></span></a>')

def galerie_raster(liste, root, css="gallery"):
    if not liste:
        return '<p class="empty">Noch keine Fotos in der Galerie.</p>'
    return f'<div class="{css}">\n' + "\n".join(
        f'      <figure><a href="{e(bild_src({"src": g["bild"]}, root))}" data-lightbox>'
        f'<img src="{e(bild_src({"src": g["bild"]}, root, True))}" alt="{e(g.get("alt") or g.get("titel") or "")}" loading="lazy"></a>'
        + (f'<figcaption>{e(g["titel"])}</figcaption>' if g.get("titel") else "") + "</figure>"
        for g in liste) + "\n    </div>"

MONATSNAMEN = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

def bewertungen_html():
    """Wechselnde Google-Bewertungen mit Gesamtbewertung und Transparenzhinweis (§ 5b UWG)."""
    if not bewertungen:
        return ""
    def monat(d):
        try:
            j, m = str(d)[:7].split("-")
            return f"{MONATSNAMEN[int(m) - 1]} {j}"
        except (ValueError, IndexError):
            return ""
    folien = "\n".join(
        f'''      <blockquote class="review{' is-active' if i == 0 else ''}">
        <div class="stars" aria-label="5 von 5 Sternen">★★★★★</div>
        <p>{"<br>".join(e(z) for z in b["text"].strip().splitlines())}</p>
        <footer><b>{e(b.get("name") or "Google-Nutzer:in")}</b> · Google-Bewertung{f" · {monat(b.get('datum'))}" if monat(b.get("datum")) else ""}</footer>
      </blockquote>'''
        for i, b in enumerate(bewertungen))
    punkte = "".join(f'<button aria-label="Bewertung {i + 1}" aria-selected="{str(i == 0).lower()}"></button>' for i in range(len(bewertungen)))
    return f'''<div class="reviews">
    <div class="reviews-summary">
      <span class="eyebrow">Google-Bewertungen</span>
      <div class="score">{e(str(google.get("sterne", "")))}</div>
      <div class="stars big" aria-hidden="true">★★★★★</div>
      <p>aus {e(str(google.get("anzahl", "")))} Bewertungen bei Google</p>
      <a class="btn ghost" href="{e(google.get("link", ""))}" target="_blank" rel="noopener">Alle Bewertungen auf Google</a>
    </div>
    <div class="review-slider" aria-roledescription="Bewertungen" aria-live="polite">
{folien}
      <div class="review-nav">
        <button class="review-prev" aria-label="Vorherige Bewertung">‹</button>
        <div class="review-dots">{punkte}</div>
        <button class="review-next" aria-label="Nächste Bewertung">›</button>
      </div>
    </div>
  </div>
  <p class="reviews-note">Auszug aus unseren Google-Bewertungen (Auswahl mit 5 Sternen), Namen gekürzt. Die Bewertungen stammen von Google-Nutzer:innen; wir prüfen nicht, ob die Verfasser:innen eine Vorstellung besucht haben. Alle Bewertungen findet ihr auf Google.</p>'''

def zelte_html(root):
    zelte = [z for z in kulturzelt.get("zelte") or [] if z.get("name")]
    if not zelte:
        return '<p class="empty">Infos zu unseren Zelten folgen in Kürze.</p>'
    karten = []
    for z in zelte:
        alt = re.sub(r"[\[\]]", "", z["name"])
        fotos = [b for b in (z.get("bilder") or [z.get("bild")]) if b]
        if len(fotos) > 1:
            # Mehrere Fotos: zum Durchwischen (Pfeile & Punkte steuert site.js)
            bilder = "".join(f'<img src="{e(bild_src({"src": b}, root, True))}" alt="{e(alt)} – Foto {i} von {len(fotos)}" loading="lazy">'
                             for i, b in enumerate(fotos, 1))
            punkte = "".join(f'<button aria-label="Foto {i}"></button>' for i in range(1, len(fotos) + 1))
            bild = (f'<div class="karussell" aria-roledescription="Bildershow" aria-label="Fotos: {e(alt)}">'
                    f'<div class="spur" tabindex="0">{bilder}</div>'
                    f'<button class="k-prev" aria-label="Vorheriges Foto">‹</button><button class="k-next" aria-label="Nächstes Foto">›</button>'
                    f'<div class="k-punkte">{punkte}</div></div>')
        elif fotos:
            bild = f'<img src="{e(bild_src({"src": fotos[0]}, root, True))}" alt="{e(alt)}" loading="lazy">'
        else:
            bild = '<div class="ph">Foto folgt</div>'
        fakten = "".join(f'<li><small>{label}</small><b>{todo(z.get(feld) or "")}</b></li>'
                         for feld, label in (("groesse", "Größe"), ("plaetze", "Plätze"), ("flaeche", "Stellfläche")) if z.get(feld))
        ausstattung = "".join(f"<li>{todo(a)}</li>" for a in z.get("ausstattung") or [] if a)
        karten.append(f'''<article class="zelt">
      <div class="zelt-bild">{bild}</div>
      <div class="zelt-text">
        <h3>{todo(z["name"])}</h3>
        <p>{todo(z.get("beschreibung") or "")}</p>
        <ul class="facts">{fakten}</ul>
        {f'<h4>Ausstattung</h4><ul class="checklist">{ausstattung}</ul>' if ausstattung else ""}
        <div class="btns"><a class="btn" href="#mietanfrage">Dieses Zelt anfragen</a></div>
      </div>
    </article>''')
    return '<div class="zelte">' + "\n".join(karten) + "</div>"

def equipment_html():
    teile = [q for q in kulturzelt.get("equipment") or [] if q.get("name")]
    if not teile:
        return ""
    return '<div class="equipment">' + "".join(
        f'<div class="box"><h3>{todo(q["name"])}</h3>' + (f'<p>{todo(q["text"])}</p>' if q.get("text") else "") + "</div>"
        for q in teile) + "</div>"

def miet_auswahl():
    namen = [re.sub(r"\[[^\]]*\]", "", z["name"]).strip() or "Zelt" for z in kulturzelt.get("zelte") or [] if z.get("name")]
    namen += [q["name"] for q in kulturzelt.get("equipment") or [] if q.get("name")]
    return "\n        ".join(f'<label class="check"><input type="checkbox" name="Mieten" value="{e(n)}"> {e(n)}</label>' for n in namen)

def content(name, root):
    text = (ROOT / "content" / name).read_text(encoding="utf-8")
    ersetzungen = {
        **{f"IMG_{k}": root + v for k, v in IMG.items()},
        "NAECHSTER_TERMIN_BADGE": naechster_termin_badge(root),
        "NAECHSTER_TERMIN_BILD": naechster_termin_bild(root),
        "ROOT": root,
        "LOGO": root + LOGO,
        "NAECHSTE_TERMINE": termin_liste(serien[:3], root, compact=True),
        "ALLE_TERMINE": termin_liste(serien, root),
        "STUECKE_KARTEN": stueck_karten(root),
        "STUECKE_VORSCHAU": stueck_karten(root, stuecke[:3], "plays drei"),
        "STUECKE_TABELLE": stueck_tabelle(root),
        "STUECK_OPTIONEN": stueck_optionen(),
        "GALERIE": galerie_raster(galerie, root, "wand"),
        "GALERIE_VORSCHAU": galerie_raster(galerie[:5], root, "mosaic"),
        "BEWERTUNGEN": bewertungen_html(),
        "ZELTE": zelte_html(root),
        "EQUIPMENT": equipment_html(),
        "MIET_AUSWAHL": miet_auswahl(),
        "GALERIE_VORSCHAU_KLEIN": galerie_raster(galerie[:4], root, "gallery mini"),
        "GOOGLE_STERNE": e(str(google.get("sterne", ""))),
        "GOOGLE_ANZAHL": e(str(google.get("anzahl", ""))),
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: ersetzungen[m[1]], text)

# ---------- Seiten schreiben ----------
SEITEN = [
    ("index.html", "start.html", "Gießener Figurentheater – Puppentheater für Kinder",
     "Puppentheater für das beste Publikum der Welt: Kinder! Öffentliche Vorstellungen im Theaterzelt sowie Gastspiele in Kitas, Schulen, Stadthallen und auf Events.", []),
    ("termine.html", "termine.html", "Termine & Tickets – Gießener Figurentheater",
     "Alle öffentlichen Vorstellungen des Gießener Figurentheaters mit Ort, Uhrzeit und Eintrittspreisen – zum Eintragen in den eigenen Kalender.", serien),
    ("veranstalter.html", "veranstalter.html", "Puppentheater buchen – für Kita, Schule, Stadtfest & Center | Gießener Figurentheater",
     "Mobiles Puppentheater und Theaterzelt buchen: Repertoire, Ablauf, Platzbedarf, Technik und Buchungsanfrage für Kitas, Schulen, Kommunen und Veranstalter.", []),
    ("stuecke/index.html", "repertoire.html", "Repertoire – Gießener Figurentheater",
     "Unsere Puppentheaterstücke: " + ", ".join(st["titel"] for st in stuecke) + ".", []),
    ("ueber-uns.html", "ueber-uns.html", "Über uns – Gießener Figurentheater",
     "Patrizia und Ricardo Sperlich vom Gießener Figurentheater: unsere Geschichte, handgemalte Bühnenbilder, professionelle Figuren und unser Theaterzelt.", []),
    ("kulturzelt.html", "kulturzelt.html", "KULTURzelt – Zelte & Equipment mieten | Gießener Figurentheater",
     "Theaterzelte und Veranstaltungs-Equipment mieten: für Stadtfeste, Kulturveranstaltungen, Firmen- und Familienfeiern – mit Bühne, Licht und Ton.", []),
    ("galerie.html", "galerie.html", "Galerie – Gießener Figurentheater",
     "Fotos vom Gießener Figurentheater: Figuren, handgemalte Bühnenbilder, Theaterzelt und Gastspiele.", []),
    ("impressum.html", "impressum.html", "Impressum – Gießener Figurentheater", "Impressum des Gießener Figurentheaters.", []),
    ("datenschutz.html", "datenschutz.html", "Datenschutz – Gießener Figurentheater", "Datenschutzerklärung des Gießener Figurentheaters.", []),
]

def schreibe(path, text):
    ziel = OUT / path
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(text, encoding="utf-8")

# Ausgabeordner frisch anlegen, Stylesheet/Skript/Bilder hineinkopieren, kleine Bildversionen erzeugen
shutil.rmtree(OUT, ignore_errors=True)
shutil.copytree(ROOT / "assets", OUT / "assets", ignore=shutil.ignore_patterns(".*"))
for bild in (ROOT / "assets" / "bilder").glob("*"):
    if bild.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        verkleinern(bild, OUT / klein_pfad("assets/bilder/" + bild.name))

for path, quelle, title, desc, evts in SEITEN:
    root = "../" * path.count("/")
    schreibe(path, layout(path, title, desc, content(quelle, root), jsonld(*events_jsonld(evts))))

for st in stuecke:
    body, eigene = stueck_seite(st)
    path = f'stuecke/{st["slug"]}.html'
    vorlage = st["vorlage"].strip()
    # „nach dem Bilderbuch …“ schließt direkt an, ein eigener Satz („Für alle Fans …“) wird abgetrennt
    trenner = " " if vorlage[:1].islower() else ". "
    desc = re.sub(r"\[[^\]]*\]", "", f'{st["titel"]} – Puppentheater{trenner if vorlage else ""}{vorlage}. {kurz_text(st)}').strip()
    desc = re.sub(r"\s+\.", ".", desc)
    titelbild = bild_absolut(st["bilder"][0]) if st["bilder"] else None
    schreibe(path, layout(path, f'{st["titel"]} – Puppentheater | {theater}', desc, body, jsonld(*events_jsonld(eigene)), titelbild))

for s in serien:
    titel, desc, body, bild = gastspiel_seite(s)
    schreibe(gastspiel_url(s), layout(gastspiel_url(s), titel, desc, body, jsonld(*events_jsonld([s])), bild))

# Sitemap & robots.txt, damit Suchmaschinen alle Seiten finden
urls = [p for p, *_ in SEITEN] + [f'stuecke/{st["slug"]}.html' for st in stuecke] + [gastspiel_url(s) for s in serien]
heute = now.date().isoformat()
schreibe("sitemap.xml",
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f'  <url><loc>{site}/{"" if u == "index.html" else u}</loc><lastmod>{heute}</lastmod></url>\n' for u in urls)
    + "</urlset>\n")
schreibe("robots.txt", "User-agent: *\nDisallow: /\n" if VORSCHAU else f"User-agent: *\nAllow: /\n\nSitemap: {site}/sitemap.xml\n")

schreibe("termine.ics", calendar(serien, f"{theater} – Termine"))
for s in serien:
    schreibe(f'kalender/{s["_id"]}.ics', calendar([s], f'{s["titel"]} in {s["ort"]["stadt"]}'))

print(f"{len(SEITEN) + len(stuecke) + len(serien)} Seiten, {len(serien)} Spielserien mit "
      f"{sum(len(s['_shows']) for s in serien)} Vorstellungen, {len(galerie)} Galerie-Fotos → {OUT.name}/")
