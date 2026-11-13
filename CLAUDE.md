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
- **Online (Vorschau seit 06.11.2026):** Repository `GiessenerFigurentheater/Website-Giessener-Figurentheater`,
  Vorschau-Link https://giessenerfigurentheater.github.io/Website-Giessener-Figurentheater/ (Pages-Quelle: GitHub Actions).
  **Hochladen nur auf Ansage:** Claude pusht erst, wenn der Nutzer ausdrücklich sagt, dass hochgeladen werden soll
  (Wunsch vom 07.11.2026). Änderungen bis dahin nur lokal bauen & in der Vorschau zeigen.
  Technik: GitHub CLI liegt in `~/.local/bin/gh`, angemeldet als GiessenerFigurentheater, Git nutzt es als Anmeldung.
  Ablauf: vor der Arbeit `git pull` (sicherheitshalber); beim Hochladen
  `git add` → `git commit` (deutsche Nachricht) → `git pull --rebase` → `git push`. Nach 1–2 Min. online.

## Stand (07.11.2026)
Fertig: Startseite (blauer Foto-Samtvorhang mit Logo, öffnet sich beim Scrollen – Shutterstock-Bild 2731195765, gekauft,
Original in ~/Downloads; Bildershow, Icons Pinsel/Maske/Herz, Bewertungen, 3 Stücke), Termine & Tickets (Kopfbild = nächste
Vorstellung, FAQ, Instagram-Rabatt), Gastspielseiten, Repertoire mit 8 Stücken (Kacheln wackeln), Galerie mit Foto-Wand &
Vollbild, Über uns (Steckbriefe, Dank, Geschichte mit Zeitleiste, „Unsere Haltung“), KULTURzelt (2 Zelte mit Wisch-Bildershow,
Equipment, Mietablauf, Mietanfrage), Veranstalterseite (Ablauf in blauen Kästchen, Technik & Platz für mobile Bühne/große
Bühne/Zelt, Bewertungen, Downloads, FAQ, Buchungsformular; keine Preise). Wischgesten auf Handy für Bildershow,
Bewertungen und Galerie-Vollbild. Vorschau online auf GitHub Pages (für Google gesperrt, `VORSCHAU = True`).
Nächster Schritt (laut Nutzer): Inhalte & Kurzbeschreibungen der einzelnen Stücke.

## Fahrplan (Stand 07.11.2026)
- **Ziel:** Website im Laufe der Woche ab 09.11.2026 live stellen (Domain giessener-figurentheater.de).
- **08.11.2026 – zuerst daran erinnern:** Ricardo installiert Google Chrome + Erweiterung „Claude in Chrome“ und meldet
  sich dort bei den Portalen an (Facebook, Eventfrog, kindaling-Partnerportal, ggf. meinestadt.de, rheinmain4family).
- **08.11.2026 – Arbeit:** Inhalte & Kurzbeschreibungen der 8 Stücke (Inhalt, Highlights, Pädagogik). Muss vor dem
  Verteilen der Termine fertig sein.
- **Termine verteilen (nach dem Live-Gang):** Claude trägt Termine per Browser („Claude in Chrome“) auf den Portalen ein:
  Ricardo meldet sich selbst an und löst Captchas, Claude füllt aus und schickt erst nach Ricardos OK ab.
  Erster Test: ein kommender Termin auf meinestadt.de. Automatische Schnittstellen gibt es bei diesen Portalen nicht
  (Recherche 07.11.); später evtl. Anfragen an Stadtmarketing Gießen (Tourismus-Hub Hessen), Kulturamt, Gießener Zeitung.
  Idee „Termin teilen“-Seite (Texte/Bilder je Portal zum Kopieren) vorerst nur im Hinterkopf.
- **Vor dem Live-Gang erledigen:** Stück-Inhalte ·
  (Formular-Dienst Fakturus läuft seit 12.11.: https://formular.fakturus.com/f/website-anfragen, Test-Mail kam an; AVV bei Fakturus anfordern) · Impressum/Datenschutz (Entwurf fertig; USt-IdNr. von Patrizia fehlt noch, AVV Fakturus abwarten, rechtlich prüfen lassen) ·
  `VORSCHAU = False` (Banner + Google-Sperre) zusammen mit Domain-Umzug · Domain bei IONOS auf GitHub Pages umstellen.

## Offene Punkte
- **Veranstalterseite:** Technik & Platz fertig; Bereich „Preise“ (inkl. Abrechnung/Storno) am 07.11.2026 entfernt.
  Referenzen-Liste fertig (12.11.). Download-Bereich als HTML-Kommentar ausgeblendet, bis Dateien da sind (Presse-Kästen auf
  den Stückseiten bleiben bewusst sichtbar – Ricardo will sie zeitnah füllen).
- **Stücke (Arbeit läuft, Stück für Stück):** Eckdaten (Alter, Dauer, Zuschauer, Spielform) + Titelfoto fertig bei
  Furzipups, NEINhorn, Familie Wutz, Grüffelo, Lulu Lavazunge. Noch offen: Kasperletheater, beide Weihnachtsstücke
  (Eckdaten; Kasperle & Peppa auch Foto). Bei allen fehlen Inhalt, Highlights, Pädagogik; Kurzbeschreibung bei Familie Wutz
  und Lulu Lavazunge; Vorlage Familie Wutz; Vorlage „Lulu Lavazunge“ bestätigen; Vorlage/Rechte „Peppa feiert Weihnachten“.
  Jede Stückseite hat den Kasten „Presse & Material“ (Feld `presse`) – Dateien fehlen noch.
  Hochkante Fotos: Feld `fokus` (oben/mitte/unten) beim Bild setzen.
  Alle 8 Stücke haben Inhalt, Highlights, Pädagogik (12.11.2026). Offen: Presse-Downloads; Mitwirkende bei Familie Wutz.
  Familie Wutz: Handlung noch offen; Texte bewusst ohne „Peppa“, „Mama/Papa Wutz“ (Markenrecht). Lulu Lavazunge: Premiere 2027.
  „Spielbar als“: Kasperletheater nur „kleine Bühne“, alle anderen „kleine Bühne, große Bühne, im Theaterzelt“.
- **Über uns:** Theaterzelt-Details, „Unsere Haltung“ („Was uns ausmacht“ wurde am 07.11.2026 entfernt).
  Zeitleiste 2026 („In diesem Jahr …“) nach dem Jahreswechsel anpassen; Rabe-Socke-Untertitel prüfen.
- **Spielorte:** Straße & PLZ der Zelt-Standorte Braunschweig und Gießen fehlen.
- **Impressum / Datenschutz:** rechtlich prüfen lassen.
- **Vor dem Live-Gang:** (Logo & alte IONOS-Fotos am 12.11.2026 nach `assets/bilder/` übernommen; Schrift seit 12.11. selbst gehostet in `assets/fonts/`) 
  `VORSCHAU = False` in `build.py` setzen – schaltet Entwurfs-Banner UND Google-Sperre (noindex, robots.txt) gemeinsam ab; erst zusammen mit dem Domain-Umzug.
- **Online bringen:** GitHub & Pages erledigt (06.11.2026); offen: Domain bei IONOS umstellen.
- **Kein Admin-Bereich (Entscheidung 12.11.2026):** Ricardo pflegt alles über Claude im Chat; Pages CMS wurde entfernt
  (`.pages.yml` gelöscht). Ricardo soll den Pages-CMS-Zugriff bei GitHub entziehen.
