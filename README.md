# KF Portionsrechner

Single-HTML-PWA zur Portions- und Einkaufsplanung für Kochaktionen der
**Knoblauchfahne** (KüFa). Offline-fähig, browser-only, keine Backend-
Installation. Läuft auf GitHub Pages.

---

## Was es kann

- **Kochaktionen planen** (Datum, Mahlzeiten, Portionszahlen)
- **Rezeptbuch** mit Zutaten, Allergenen, Tags, Kochfaktor und Saisonalität
- **Standardmahlzeiten** als Vorlagen
- **Einkaufslisten** generieren
  - Grundbedarfe (aggregiert)
  - Nach Rezept gruppiert
  - Export als TXT / CSV / PDF
- **Rezept-Druck** als A4-PDF pro Rezept (Zutaten mit Brutto/Netto/gekocht,
  Zubereitungsanleitung, Platz für Notizen)
- **Saisonkalender** — gespeist direkt aus den Zutaten
- **DE/EN** durchgängig umschaltbar
- **Offline** durch Service Worker; automatischer Update-Check
- **Backup/Restore** des kompletten Datenbestands als JSON

---

## Technik auf einen Blick

| Bereich        | Wahl                                                     |
|----------------|----------------------------------------------------------|
| Build          | _keiner_ — reine `index.html` direkt im Browser          |
| Speicher       | IndexedDB (Datenbank-Version siehe `DB_VERSION`)         |
| Offline        | Service Worker (`sw.js`), Stale-while-revalidate         |
| UI             | eigener Mini-Builder `h(tag, attrs, ...children)`        |
| i18n           | `I18N = { de: {…}, en: {…} }` + `t('key', …args)`        |
| PDF            | `window.open` + `window.print` (keine externe Library)   |
| Hosting        | GitHub Pages (`https://<user>.github.io/Kuefa-calculator`) |

---

## Dateien

```
index.html           — komplette App (Meta, CSS, HTML, JS)
sw.js                — Service Worker (App-Shell-Cache, Update-Check)
standardbackup.json  — „Standard laden"-Datenbestand (Zutaten, Rezepte,
                        Kategorien, Tags, Allergene, Präparationsmethoden …)
README.md            — diese Datei
```

Keine weiteren Abhängigkeiten, kein `package.json`, kein Build-Schritt.

---

## Architektur

```
┌──────────────────────── index.html ────────────────────────┐
│  <head>  Meta, PWA-Manifest (base64), SVG-Favicon          │
│  <style> Design-Tokens, Base, Komponenten, Responsive      │
│  <body>  Grundgerüst (Sidebar, Content, Modal-Root)        │
│  <script>                                                   │
│    ┌── i18n ──────────────────────────────────────┐        │
│    ├── Database (IndexedDB-CRUD, Entity-Getter)   │        │
│    ├── App State (let-Globals)                    │        │
│    ├── Helpers (h, showModal, downloadFile, …)    │        │
│    ├── Theme / Sidebar / Nav                      │        │
│    ├── Pages (Calendar, Ingredients, Recipes, …)  │        │
│    ├── Service Worker (Update-Banner)             │        │
│    └── Init (openDB → renderNav → page)           │        │
└────────────────────────────────────────────────────────────┘
                        │ persistiert
                        ▼
                   IndexedDB (Browser)
                        ▲
                        │ initial befüllt aus
                   standardbackup.json
```

### Datenmodell (gekürzt)

```
actions ── cooking_days ── meal_slots ── assignments ─┐
                                                      ▼
subcategories ─ ingredients ─ ingredient_allergens   recipes
                         │                            │
                         │    ingredient_tags         │   recipe_categories
                         │                            │   recipe_allergens
                         │                            │   recipe_tags
                         │          recipe_ingredients│
                         └──────────────▲─────────────┘
                                        │
                    recipe_ingredient_substitutes
```

Alle Stores mit `id` als Auto-Increment-Key. IDs aus dem Backup werden
übernommen, neue Einträge bekommen frische IDs vom Browser.

### Saisonalität (seit Nov 2026)

Saison-Daten liegen **direkt an der Zutat** (nicht mehr in einer Liste
irgendwo):

- `season_category`: `'Gemüse' | 'Obst' | 'Kräuter' | ''`
- `months`: `number[12]` mit je `0` (nicht verfügbar), `1` (Lager),
  `2` (frisch/Freiland), Reihenfolge Jan–Dez

Der Saisonkalender zeigt automatisch alle Zutaten mit gesetzter
`season_category` und mindestens einem Monat > 0.

Per Zutat gibt es in der Zutatenliste einen 📅-Button für einen
fokussierten Quick-Dialog (nur Kategorie + Monate), unabhängig vom
vollen Bearbeiten-Dialog.

---

## Entwickeln

### Lokal starten

Ein lokaler Webserver ist nötig (kein `file://` — der Service Worker und
`fetch('standardbackup.json')` funktionieren nur über HTTP). Einfachste
Varianten:

```bash
# Python
python -m http.server 8000

# Node
npx serve .
```

Dann im Browser `http://localhost:8000`.

### Änderungen einspielen

1. `index.html` bearbeiten
2. `DB_VERSION` erhöhen **nur** wenn sich Objekt-Stores/Indizes ändern
3. Syntax-Check (es gibt keinen Build, aber `node --check` via Skript geht):

   ```bash
   node -e "const h=require('fs').readFileSync('index.html','utf8'); \
     const re=/<script(?:\\s[^>]*)?>([\\s\\S]*?)<\\/script>/g; \
     let m; while((m=re.exec(h))) new Function(m[1]);"
   ```

4. Browser hart neu laden (Service Worker erkennt neue Version automatisch
   und zeigt einen Update-Banner)

### Commits

- Kleine, thematische Commits (ein Zweck pro Commit)
- Präfixe: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- Claude-Co-Author-Zeile am Ende bleibt drin

---

## Konventionen

### JavaScript

- **Sprache**: ES2020+. Optional-Chaining, async/await, Spread/Rest
- **Einrückung**: 2 Spaces. Einzel-Quotes. Semikolons.
- **Namen**:
  - Funktionen: `verbObject` (`renderRecipePage`, `loadSeasonEntries`)
  - Daten: Nomen (`recipes`, `seasonEntries`)
  - Booleans: `is…`, `has…`, `can…`
  - Konstanten: `SCREAMING_SNAKE_CASE`
- **DOM**: immer über `h(tag, attrs, ...children)` — keine rohen
  `document.createElement` in der App-Logik
- **Texte**: immer durch `t('key', …)` — **nie** hardcoded DE/EN
- **Dialoge**: `showModal(…)` + `closeModal(…)`
- **Fehler-Feedback**: `alert(t('msg_…'))` (wird später durch Toast ersetzt)

### CSS

- Design-Tokens in `:root` (Dark) und `:root.light`
- Komponentennamen als Klassen (`.card`, `.btn`, `.modal`, …)
- Mobile-Breakpoint `@media (max-width: 768px)`
- Inline-Styles in JS nur für dynamische Werte — alles Statische als Klasse

### i18n

- Jeder neue sichtbare Text bekommt **beide** Keys (`de` + `en`)
- Key-Konvention: `bereich_zweck` (`btn_save`, `lbl_name`, `msg_confirm_delete`)
- Platzhalter: `{0}`, `{1}`, … via `t('key', value)`

### Commits / PRs

- Keine WIP-Skripte committen (temporäre Node-Migrationen direkt löschen)
- `standardbackup.json` wird als normale Datei versioniert (nicht auto-generiert)

---

## Roadmap / offene Baustellen

Der Code ist historisch gewachsen, es gibt bekannte Kandidaten für
Refactoring. In Arbeit / geplant:

- [ ] **i18n gruppieren** (aktuell ~1000 flache Keys je Sprache)
- [ ] **Dialog-Helper** (`buildFormDialog`) — der Dialog-Aufbau wiederholt
      sich in Ingredient-, Recipe-, Season-, Tag-, Category-Dialog
- [ ] **Export-Pipeline vereinheitlichen** — `aggregateOrderItems()` +
      `formatTxt/Csv/Pdf`, die Datenaufbereitung ist dupliziert
- [ ] **App-State bündeln** — viele `let`-Globals zentralisieren
- [ ] **Inline-Styles → CSS-Klassen**, wo die Werte statisch sind
- [ ] **Toast statt `alert`** für User-Feedback

---

## Lizenz / Autor

Internes Werkzeug der Küchenfanfare / Knoblauchfahne. Noch keine
öffentliche Lizenz hinterlegt.
