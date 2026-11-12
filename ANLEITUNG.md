# Website Gießener Figurentheater – Anleitung

## So funktioniert es

```
Ricardo sagt Claude im Chat, was sich ändern soll
   →  Claude ändert die Dateien hier im Ordner und zeigt die Vorschau
   →  auf „hochladen“ hin: speichert in GitHub
   →  GitHub baut die Website (1–2 Minuten, zusätzlich jede Nacht)  →  online
```

Jede Nacht wird die Website automatisch neu gebaut – vergangene Vorstellungen verschwinden dadurch
von selbst, auch wenn niemand etwas ändert.

---

## Im Alltag (einfach Claude im Chat sagen)

**Neuer Termin** – z. B.: „Neuer Termin: Der Grüffelo im Theaterzelt Wetzlar, Musterstraße 1, 35578 Wetzlar,
vom 14. bis 16. März 2027, Freitag 16 Uhr, Samstag und Sonntag 11 und 15 Uhr, Eintritt 9 € / Kinder 7 €.“
Daraus entstehen automatisch: Terminkarte, Gastspielseite, Google-Daten, Kalender-Einträge.

**Abgesagt, ausverkauft, verschoben** – „Die Vorstellung am … ist ausverkauft / abgesagt.“

**Neues Stück, neue Fotos, Texte ändern** – Fotos einfach in den Chat ziehen und dazuschreiben, wohin sie sollen.

**Hochladen** – Claude lädt erst hoch, wenn ihr ausdrücklich „hochladen“ sagt. Bis dahin sind Änderungen nur
in der Vorschau auf dem Mac zu sehen.

---

## Wo liegt was? (falls einmal jemand anderes übernimmt)

Alle Daten liegen **doppelt**: in diesem Ordner auf dem Mac und als vollständige Kopie mit allen früheren
Versionen bei GitHub (Repository `GiessenerFigurentheater/Website-Giessener-Figurentheater`).
Jedes andere KI-Werkzeug oder jede Webentwicklerin kann damit weiterarbeiten – die Notiz `CLAUDE.md`
beschreibt Aufbau, Arbeitsweise und offene Punkte.

| Ordner / Datei            | Inhalt                                                          |
|---------------------------|-----------------------------------------------------------------|
| `inhalte/termine.json`    | Spielserien (Ort, Zeitraum, Uhrzeiten, Preise, Status)          |
| `inhalte/stuecke/*.json`  | Ein Stück pro Datei (Texte, Eckdaten, Bilder, Mitwirkende)      |
| `inhalte/galerie.json`    | Galerie-Fotos (die ersten 5 auch auf der Startseite)            |
| `inhalte/kulturzelt.json` | Zelte & Equipment zur Vermietung                                |
| `inhalte/bewertungen.json`, `inhalte/google.json` | Google-Bewertungen                      |
| `content/*.html`          | Feste Seitentexte (Startseite, Veranstalter, Impressum …)       |
| `assets/bilder/`          | Alle Bilder · `assets/fonts/` Schrift · `assets/style.css` Design |
| `build.py`                | Baut die Website nach `_site/` (Python 3)                       |
| `.github/workflows/`      | Automatisches Bauen & Veröffentlichen bei GitHub                 |

Lokal ansehen: `python3 build.py`, danach `python3 vorschau.py` und <http://localhost:8765> öffnen.

**Tipp:** Eine Time-Machine-Sicherung des Macs schützt zusätzlich – auch wenn GitHub ohnehin eine Kopie hat.

---

## Zugänge (nur für euch – nicht weitergeben)

- **GitHub:** Konto „GiessenerFigurentheater“. Die Website ist im Repository öffentlich einsehbar, das ist für
  die kostenlose Veröffentlichung nötig; dort liegen nur Website-Inhalte.
- **Fakturus Formular:** Formular „website-anfragen“ – Anfragen von der Website kommen per E-Mail an.
- **IONOS:** Domain giessener-figurentheater.de.

---

## Eigene Domain umziehen (beim Live-Gang, Claude führt durch)

- GitHub: **Settings → Pages → Custom domain**: `www.giessener-figurentheater.de` eintragen,
  danach „Enforce HTTPS“ anhaken.
- IONOS (Domain-Verwaltung → DNS):
  - `www` als **CNAME** auf `giessenerfigurentheater.github.io`
  - die Hauptdomain (`@`) als **A-Einträge** auf
    `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
- Die Umstellung dauert meist wenige Stunden. Danach kann der IONOS-Baukasten gekündigt werden
  (die Domain selbst bleibt bei IONOS).
