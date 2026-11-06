# Website Gießener Figurentheater – Anleitung

## So funktioniert es

```
Admin-Bereich (Pages CMS)  →  speichert in GitHub  →  GitHub baut die Website  →  online
     app.pagescms.org          (alle Inhalte)          (1–2 Minuten, + jede Nacht)
```

Ihr pflegt alles im Browser – am Computer oder am Handy. Nach dem Speichern ist die Änderung
nach 1–2 Minuten online. Jede Nacht wird die Website zusätzlich neu gebaut, damit vergangene
Vorstellungen automatisch verschwinden.

---

## Einmalig einrichten

### 1. GitHub-Konto anlegen
- Auf <https://github.com/signup> ein kostenloses Konto anlegen.

### 2. Die Website zu GitHub hochladen
- Auf GitHub ein neues Repository anlegen, z. B. mit dem Namen `website`
  (Sichtbarkeit: **Public** – für die kostenlose Veröffentlichung nötig; dort liegen nur die Website-Inhalte).
- Die Dateien aus diesem Ordner hochladen (Claude kann das übernehmen, sobald das Repository existiert).

### 3. Automatisches Veröffentlichen einschalten
- Im Repository: **Settings → Pages → Build and deployment → Source: „GitHub Actions“**.
- Unter **Actions** erscheint danach „Website veröffentlichen“. Nach ein paar Minuten ist die Seite
  unter `https://<euer-name>.github.io/website/` erreichbar – zum Testen, bevor die echte Domain umzieht.

### 4. Admin-Bereich verbinden
- <https://app.pagescms.org> öffnen → **Sign in with GitHub**.
- Der Pages-CMS-App Zugriff auf das Repository `website` erlauben.
- Repository auswählen – links erscheinen **Termine**, **Repertoire (Stücke)** und **Galerie**.

### 5. Eigene Domain umziehen (wenn alles passt)
- GitHub: **Settings → Pages → Custom domain**: `www.giessener-figurentheater.de` eintragen,
  danach „Enforce HTTPS“ anhaken.
- IONOS (Domain-Verwaltung → DNS):
  - `www` als **CNAME** auf `<euer-name>.github.io`
  - die Hauptdomain (`@`) als **A-Einträge** auf
    `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
- Die Umstellung dauert meist wenige Stunden. Danach kann der IONOS-Baukasten gekündigt werden
  (die Domain selbst bleibt bei IONOS).

---

## Im Alltag

### Neuen Termin eintragen
1. **Termine** öffnen → **Hinzufügen**.
2. **Stück** auswählen – Bild, Altersangabe und Stückseite werden automatisch verknüpft.
3. Titel, Kurzbeschreibung, Spielort (mit Straße & PLZ – wichtig für Google), erster und letzter Spieltag.
4. **Spielzeiten je Wochentag**: z. B. Freitag `16:00`, Sonntag `11:00, 14:00`. Leere Wochentage = keine Vorstellung.
5. Optional: Tage ohne Vorstellung, Zusatzvorstellungen, eigenes Bild.
6. Eintrittspreise eintragen → **Speichern**.

Daraus entstehen automatisch: Terminkarte, eigene Gastspielseite, Google-Daten für jede einzelne
Vorstellung, Kalender-Einträge und der Eintrag im Kalender-Abo.

**Abgesagt oder ausverkauft?** Beim Termin den **Status** ändern – das erscheint auf der Website
und wird auch an Google gemeldet.

### Neues Stück anlegen
1. **Repertoire (Stücke)** → **Hinzufügen**.
2. Titel, Kurzbeschreibung, Alter, Dauer usw. ausfüllen.
3. **Bilder** hinzufügen – das erste Bild ist das Titelbild. Bitte immer eine kurze Bildbeschreibung
   eintragen (hilft Google und Menschen mit Sehbehinderung).
4. **Speichern** → das Stück erscheint im Repertoire, bekommt eine eigene Unterseite und steht
   im Anfrageformular für Veranstalter zur Auswahl.

Ein Stück vorübergehend ausblenden: Haken bei **„Auf der Website zeigen“** entfernen.
Reihenfolge im Repertoire: Feld **Reihenfolge** (kleinere Zahl = weiter vorne).

Tipp: Texte in `[eckigen Klammern]` werden auf der Website gelb markiert – praktisch für Notizen,
was noch fehlt. Vor dem Live-Gang alle eckigen Klammern entfernen.

### Galerie
- **Galerie** öffnen → **Hinzufügen** → Foto hochladen, Bildunterschrift und Bildbeschreibung eintragen.
- Neue Fotos nach **oben** ziehen: Die ersten 5 erscheinen auch auf der Startseite.
- **Foto entfernen:** den Eintrag löschen und speichern. Die Datei selbst kann zusätzlich unter
  **Media** gelöscht werden.
- Fotos am besten im Querformat und höchstens ca. 2.000 Pixel breit hochladen.
  Kleine Versionen fürs Handy werden automatisch erzeugt.

### Etwas schiefgegangen?
- Jede Änderung wird in GitHub gespeichert und kann dort wiederhergestellt werden.
- Ob die Website neu gebaut wurde, seht ihr im Repository unter **Actions**
  (grüner Haken = online, rotes X = Fehler – dann die zuletzt gespeicherte Änderung prüfen).

---

## Für Technik-Interessierte

| Ordner / Datei            | Inhalt                                                          |
|---------------------------|-----------------------------------------------------------------|
| `inhalte/termine.json`    | Spielserien (wird im Admin-Bereich unter „Termine“ gepflegt)    |
| `inhalte/stuecke/*.json`  | Ein Stück pro Datei                                             |
| `inhalte/galerie.json`    | Galerie-Fotos                                                   |
| `assets/bilder/`          | Hochgeladene Bilder                                             |
| `content/*.html`          | Feste Seitentexte (Startseite, Veranstalter, Impressum …)       |
| `assets/style.css`        | Design                                                          |
| `build.py`                | Baut die Website nach `_site/`                                  |
| `.pages.yml`              | Formulare des Admin-Bereichs                                    |
| `.github/workflows/`      | Automatisches Bauen & Veröffentlichen                           |

Lokal ansehen: `python3 build.py`, danach `python3 -m http.server 8765 --directory _site`
und <http://localhost:8765> öffnen.
