# Website Gießener Figurentheater – Projektnotiz

Neue Website für das Gießener Figurentheater (Patrizia & Ricardo Sperlich, Wettenberg).
Statische Website, erzeugt von `build.py` (Python 3.9-kompatibel halten – auf dem Mac läuft 3.9).
Sprache der Website und der Kommunikation: Deutsch, Besucher werden mit „ihr“ angesprochen.

## Aufbau
| Pfad | Inhalt |
|---|---|
| `content/*.html` | Feste Seitentexte (start, termine, veranstalter, repertoire, galerie, ueber-uns, impressum, datenschutz). Platzhalter `{{…}}` füllt `build.py`. |
| `inhalte/stuecke/*.json` | Ein Stück pro Datei → Karte im Repertoire + Unterseite `stuecke/<datei>.html` |
| `inhalte/termine.json` | Spielserien (Wochentags-Rhythmus, Ausfälle, Zusatztermine, Preise, optional Bild & Vorverkauf; Spieldauer kommt immer vom Stück, „ca.“ ergänzt der Build automatisch) → Terminkarten, Gastspielseiten `gastspiele/…`, Schema.org-Events, iCal |
| `inhalte/galerie.json` | Galerie; die ersten 5 Fotos erscheinen auch auf der Startseite |
| `inhalte/kulturzelt.json` | Zelte (Feld `bilder`: mehrere Fotos = Bildershow zum Durchwischen) & Equipment zur Vermietung → Seite `kulturzelt.html` (mit Mietanfrage-Formular) |
| `inhalte/bewertungen.json`, `inhalte/google.json` | Ausgewählte 5-Sterne-Google-Bewertungen + Gesamtbewertung (Startseite & Veranstalter) |
| `assets/` | `style.css`, `site.js`, `bilder/` (kleine Handy-Versionen erzeugt der Build in `_site/assets/bilder/klein/`), `downloads/` (Pressetext, Pressefotos, Plakat je Stück – Feld `presse` in der Stück-Datei) |
| `_site/` | Fertige Website (wird bei jedem Build komplett neu erzeugt, nicht von Hand bearbeiten) |
| `.pages.yml` | Formulare des Admin-Bereichs (Pages CMS) |
| `.github/workflows/website.yml` | Bauen & Veröffentlichen auf GitHub Pages (bei Push + jede Nacht) |
| `ANLEITUNG.md` | Anleitung für Patrizia & Ricardo (Einrichtung, Alltag) |

Texte in `[eckigen Klammern]` (JSON) bzw. `<mark class="todo">` (HTML) erscheinen gelb = noch offen.

## Arbeiten
- Bauen: `python3 build.py`
- Vorschau: Die Vorschau-Funktion der App darf nicht auf „Dokumente“ zugreifen (macOS). Stattdessen
  im Hintergrund `python3 vorschau.py` starten (Server ohne Browser-Cache, Port 8765) und
  `http://localhost:8765` im Browser öffnen. Nicht `python3 -m http.server` nehmen – der Browser zeigt sonst
  alte Seiten aus dem Zwischenspeicher. Stylesheet/Skript tragen einen Versions-Stempel (`?v=…`).
- Jede Änderung im Browser prüfen (Desktop 1280 px und Handy 375 px, kein seitliches Scrollen).

## Stand (31.10.2026)
Fertig: Startseite (Bildershow, Bewertungen, 3 Stücke als Vorschau), Termine & Tickets (Instagram-Rabatt,
FAQ), Gastspielseiten, Repertoire mit 8 Stücken, Galerie mit Vollbild, Über uns (Steckbriefe, Dank,
Geschichte mit Zeitleiste 1970–2026), Veranstalterseite (Ablauf, Technik, Preise, Bewertungen, FAQ,
Buchungsformular), Admin-Bereich vorbereitet, Vorverkaufs-Feld für Termine.

## Offene Punkte
- **Veranstalterseite:** Technik & Platz (Maße, Strom, Auf-/Abbau für mobile Bühne, große Bühne, Zelt),
  Preise & Leistungen, MwSt./KSK, Storno, weitere Spielorte (u. a. Rerik, Celle ergänzen), Downloads (Dateien fehlen).
- **Stücke (Arbeit läuft, Stück für Stück):** Eckdaten (Alter, Dauer, Zuschauer, Spielform) + Titelfoto fertig bei
  Furzipups, NEINhorn, Familie Wutz, Grüffelo, Lulu Lavazunge. Noch offen: Kasperletheater, beide Weihnachtsstücke
  (Eckdaten; Kasperle & Peppa auch Foto). Bei allen fehlen Inhalt, Highlights, Pädagogik; Kurzbeschreibung bei Familie Wutz
  und Lulu Lavazunge; Vorlage Familie Wutz; Vorlage „Lulu Lavazunge“ bestätigen; Vorlage/Rechte „Peppa feiert Weihnachten“.
  Jede Stückseite hat den Kasten „Presse & Material“ (Feld `presse`) – Dateien fehlen noch.
  Hochkante Fotos: Feld `fokus` (oben/mitte/unten) beim Bild setzen.
  Offene Frage: Schlagwort „Neu“ bei „Furzipups der Knatterdrache“ (Premiere war 2024).
- **Über uns:** „Was uns ausmacht“ (Bühnenbilder → Swen Richert; Figuren → Till de Kock / heutige Ateliers –
  Nutzer wollte das später füllen), Theaterzelt-Details, „Unsere Haltung“.
  Zeitleiste 2026 („In diesem Jahr …“) nach dem Jahreswechsel anpassen; Rabe-Socke-Untertitel prüfen.
- **Spielorte:** Straße & PLZ der Zelt-Standorte Braunschweig und Gießen fehlen.
- **Impressum / Datenschutz:** rechtlich prüfen lassen.
- **Vor dem Live-Gang:** Logo und ältere Fotos liegen noch auf der alten IONOS-Seite (nur mit OK des Nutzers
  herunterladen und nach `assets/bilder/` übernehmen); Google Fonts selbst hosten; Formular-Dienst anbinden;
  gelbes Entwurfs-Banner in `build.py` entfernen; `VORSCHAU = False` in `build.py` setzen (sonst bleibt die Seite für Google gesperrt: noindex + robots.txt Disallow).
- **Online bringen:** GitHub-Konto & Repository, Upload, Pages auf „GitHub Actions“, Pages CMS verbinden
  (Stück-Auswahl beim Termin und Dateinamen neuer Stücke dabei live prüfen), Domain bei IONOS umstellen.
