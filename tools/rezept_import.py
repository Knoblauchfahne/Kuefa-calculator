#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rezept-Konverter für den KüFa Organizer.

Wandelt Rezepte von Websites (schema.org/Recipe-JSON-LD), aus Markdown- oder
Textdateien in das Text-Importformat des Rezeptbuchs um ("=== REZEPT ===").
Die erzeugte Datei wird in der App über Rezeptbuch → Import eingelesen.

Zutaten werden gegen die standardbackup.json abgeglichen (exakt, dann unscharf),
damit vorhandene Zutaten wiederverwendet statt doppelt angelegt werden.

Aufrufe:
    py tools/rezept_import.py https://www.chefkoch.de/rezepte/...
    py tools/rezept_import.py rezept.md anderes.txt -o import.txt
    py tools/rezept_import.py rezept.md --personen 4
    py tools/rezept_import.py --server        # für den „Umwandeln"-Knopf in der App

Markdown-/Text-Konvention (Abschnitte werden per Überschrift erkannt):
    # Gemüsecurry
    Portionen: 4            (alternativ: "Für 4 Personen" im Text)
    Beschreibung: ...       (optional)
    Tags: vegan, indisch    (optional)

    ## Zutaten
    - 500 g Kartoffeln, geschält
    - 2 EL Öl
    - Salz

    ## Zubereitung
    1. ...

    ## Hinweis                (optional)
    ...

Ist die Bibliothek recipe-scrapers installiert (pip install recipe-scrapers),
wird sie automatisch als Fallback für Websites ohne lesbares JSON-LD genutzt.
"""
import argparse
import difflib
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

# Windows-Konsolen sind oft nicht UTF-8 — Ausgabe robust machen
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

# ── Einheiten-Normalisierung auf die App-Einheiten ────────────────
UNIT_MAP = {
    'g': 'g', 'gr': 'g', 'gramm': 'g',
    'kg': 'kg', 'kilo': 'kg', 'kilogramm': 'kg',
    'l': 'L', 'liter': 'L', 'ltr': 'L',
    'ml': 'ml', 'milliliter': 'ml',
    'el': 'EL', 'esslöffel': 'EL', 'eßlöffel': 'EL', 'essloeffel': 'EL',
    'tl': 'TL', 'teelöffel': 'TL', 'teeloeffel': 'TL',
    'stück': 'Stück', 'stk': 'Stück', 'st': 'Stück', 'stuck': 'Stück', 'stücke': 'Stück',
    'bund': 'Bund', 'bd': 'Bund',
    'dose': 'Dose(n)', 'dosen': 'Dose(n)', 'dose(n)': 'Dose(n)',
    'packung': 'Packung', 'päckchen': 'Packung', 'pck': 'Packung', 'pkg': 'Packung',
    'pack': 'Packung', 'pkt': 'Packung',
    'becher': 'Becher',
    # englische Einheiten (recipe-scrapers / englische Seiten)
    'tbsp': 'EL', 'tablespoon': 'EL', 'tablespoons': 'EL',
    'tsp': 'TL', 'teaspoon': 'TL', 'teaspoons': 'TL',
    'piece': 'Stück', 'pieces': 'Stück',
    'can': 'Dose(n)', 'cans': 'Dose(n)',
}
# Einheiten, die die App nicht kennt, aber sinnvoll durchgereicht werden
PASSTHROUGH_UNITS = {'prise', 'prisen', 'zehe', 'zehen', 'scheibe', 'scheiben',
                     'kopf', 'köpfe', 'knolle', 'knollen', 'stange', 'stangen',
                     'zweig', 'zweige', 'blatt', 'blätter', 'würfel', 'tasse', 'tassen',
                     'msp', 'messerspitze', 'schuss', 'spritzer', 'handvoll', 'glas', 'gläser',
                     'paar'}

FRACTIONS = {'½': .5, '⅓': 1/3, '⅔': 2/3, '¼': .25, '¾': .75, '⅕': .2,
             '⅛': .125, '⅜': .375, '⅝': .625, '⅞': .875}

OPTIONAL_MARKERS = ('nach belieben', 'n. b.', 'n.b.', 'optional', 'nach geschmack')


# Im Server-Modus werden Meldungen pro Anfrage gesammelt statt gedruckt
_report = None


def warn(msg):
    if _report is not None:
        _report.append(f'⚠ {msg}')
    else:
        print(f'  ⚠ {msg}', file=sys.stderr)


def info(msg):
    if _report is not None:
        _report.append(msg.strip())
    else:
        print(msg, file=sys.stderr)


# ── Zahlen / Mengen ───────────────────────────────────────────────
def parse_number(s):
    """'1,5' | '1 1/2' | '½' | '2-3' → float (bei Bereichen: Mittelwert)."""
    s = s.strip()
    for ch, val in FRACTIONS.items():
        if ch in s:
            rest = s.replace(ch, '').strip()
            base = parse_number(rest) if rest else 0
            return (base or 0) + val
    s = s.replace(',', '.')
    m = re.match(r'^(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)$', s)  # Bereich
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2
    m = re.match(r'^(\d+)\s+(\d+)\s*/\s*(\d+)$', s)  # 1 1/2
    if m:
        return int(m.group(1)) + int(m.group(2)) / int(m.group(3))
    m = re.match(r'^(\d+)\s*/\s*(\d+)$', s)  # 1/2
    if m:
        return int(m.group(1)) / int(m.group(2))
    m = re.match(r'^\d+(?:\.\d+)?', s)
    return float(m.group(0)) if m else None


def fmt_number(x):
    """Float → String mit Punkt, max. 4 Nachkommastellen, ohne Nullen-Schwanz."""
    s = f'{round(x, 4):.4f}'.rstrip('0').rstrip('.')
    return s or '0'


def parse_ingredient_line(line):
    """'500 g Kartoffeln, geschält (vorwiegend festkochend)'
       → dict(name, prep, qty, unit, optional)"""
    raw = line.strip().lstrip('-*•').strip()
    if not raw:
        return None
    # Plural-Marker à la Chefkoch: "Zwiebel(n)" → "Zwiebeln", "Möhre(n)" → "Möhren"
    raw = re.sub(r'\((n|en|e|s)\)', r'\1', raw)
    # Füllwörter ohne Mengenaussage am Anfang entfernen: "etwas Thymian" → "Thymian"
    raw = re.sub(r'^(etwas|ca\.?|evtl\.?|ggf\.?|einige)\s+', '', raw, flags=re.I)
    optional = any(m in raw.lower() for m in OPTIONAL_MARKERS)
    # Klammer-Zusätze in die Verarbeitung verschieben
    parens = re.findall(r'\(([^)]*)\)', raw)
    raw = re.sub(r'\s*\([^)]*\)', '', raw).strip()
    for m in OPTIONAL_MARKERS:
        raw = re.sub(re.escape(m), '', raw, flags=re.I).strip(' ,;')

    qty = None
    unit = ''
    rest = raw
    m = re.match(r'^([\d.,/\s½⅓⅔¼¾⅕⅛⅜⅝⅞–-]+)\s*(.*)$', raw)
    if m and m.group(1).strip():
        qty = parse_number(m.group(1))
        rest = m.group(2).strip()
    if qty is not None and rest:
        first, _, tail = rest.partition(' ')
        key = first.lower().strip('.')
        if key in UNIT_MAP:
            unit = UNIT_MAP[key]
            rest = tail.strip()
        elif key in PASSTHROUGH_UNITS:
            unit = first.strip('.')
            rest = tail.strip()
    name, _, prep = rest.partition(',')
    name = name.strip()
    prep = prep.strip()
    if parens:
        prep = (prep + ('; ' if prep else '') + '; '.join(p.strip() for p in parens)).strip()
    if not name:
        return None
    if qty is None:
        qty = 0
    if not unit:
        unit = 'Stück' if qty and float(qty) == int(float(qty)) else 'Stück'
    return {'name': name, 'prep': prep, 'qty': qty, 'unit': unit, 'optional': optional}


# ── Zutaten-Abgleich gegen standardbackup.json ────────────────────
def _norm(s):
    s = s.casefold().strip()
    for a, b in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')):
        s = s.replace(a, b)
    return re.sub(r'\s+', ' ', s)


class IngredientMatcher:
    def __init__(self, backup_path=None, names=None):
        self.names = []          # Original-DB-Namen
        self.by_norm = {}
        if names is not None:
            for n in names:
                if n:
                    self.names.append(n)
                    self.by_norm[_norm(n)] = n
        elif backup_path and backup_path.exists():
            data = json.loads(backup_path.read_text(encoding='utf-8'))
            for ing in data.get('ingredients', []):
                n = ing.get('name', '')
                if n:
                    self.names.append(n)
                    self.by_norm[_norm(n)] = n
            info(f'Zutaten-Abgleich: {len(self.names)} Zutaten aus {backup_path.name} geladen')
        else:
            warn('standardbackup.json nicht gefunden — Abgleich deaktiviert, '
                 'alle Zutaten werden ggf. neu angelegt')

    def match(self, name):
        """→ (db_name | original, art) mit art ∈ exakt|singular|fuzzy|neu"""
        if not self.names:
            return name, 'neu'
        n = _norm(name)
        if n in self.by_norm:
            return self.by_norm[n], 'exakt'
        # Singular/Plural-Heuristik: Karotte↔Karotten, Zwiebel↔Zwiebeln
        for cand in (n + 'n', n + 'en', n + 'e', n[:-1], n[:-2]):
            if cand and cand in self.by_norm:
                return self.by_norm[cand], 'singular'
        close = difflib.get_close_matches(n, list(self.by_norm), n=1, cutoff=0.87)
        if close:
            return self.by_norm[close[0]], 'fuzzy'
        return name, 'neu'


# ── Quelle 1: Website (JSON-LD, optional recipe-scrapers) ─────────
def fetch_url(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) KueFa-Rezept-Import',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Encoding': 'identity',
        'Accept-Language': 'de,en;q=0.8',
    })
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read()
        ctype = resp.headers.get('Content-Type', '')
    m = re.search(r'charset=([\w-]+)', ctype)
    enc = m.group(1) if m else 'utf-8'
    try:
        return raw.decode(enc, errors='replace')
    except LookupError:
        return raw.decode('utf-8', errors='replace')


def iso_duration_to_min(s):
    if not s or not isinstance(s, str):
        return ''
    m = re.match(r'^P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?', s)
    if not m or (m.group(1) is None and m.group(2) is None):
        return ''
    minutes = int(m.group(1) or 0) * 60 + int(m.group(2) or 0)
    return f'{minutes} min' if minutes else ''


def _find_recipe_node(node):
    """JSON-LD rekursiv nach @type=Recipe durchsuchen."""
    if isinstance(node, list):
        for item in node:
            r = _find_recipe_node(item)
            if r:
                return r
        return None
    if isinstance(node, dict):
        t = node.get('@type', '')
        types = t if isinstance(t, list) else [t]
        if any(str(x).lower() == 'recipe' for x in types):
            return node
        for key in ('@graph', 'mainEntity', 'itemListElement'):
            if key in node:
                r = _find_recipe_node(node[key])
                if r:
                    return r
    return None


def _instructions_text(instr):
    if isinstance(instr, str):
        return _strip_html(instr)
    parts = []
    if isinstance(instr, list):
        for step in instr:
            if isinstance(step, str):
                parts.append(_strip_html(step))
            elif isinstance(step, dict):
                if step.get('@type') == 'HowToSection':
                    name = step.get('name', '')
                    if name:
                        parts.append(f'— {name} —')
                    parts.append(_instructions_text(step.get('itemListElement', [])))
                else:
                    parts.append(_strip_html(step.get('text', '') or step.get('name', '')))
    return '\n'.join(f'{p}' for p in parts if p)


def _strip_html(s):
    return html.unescape(re.sub(r'<[^>]+>', ' ', s or '')).replace('\xa0', ' ').strip()


def _parse_yield(y):
    if isinstance(y, list):
        y = y[0] if y else ''
    m = re.search(r'\d+', str(y))
    return int(m.group(0)) if m else None


def recipe_from_url(url):
    try:
        page = fetch_url(url)
    except Exception as e:
        warn(f'Konnte {url} nicht laden: {e}')
        return try_recipe_scrapers(url)
    node = None
    for m in re.finditer(r'<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         page, re.S | re.I):
        try:
            data = json.loads(m.group(1).strip(), strict=False)
        except json.JSONDecodeError:
            continue
        node = _find_recipe_node(data)
        if node:
            break
    if not node:
        info(f'  Kein Rezept-JSON-LD auf der Seite gefunden — versuche recipe-scrapers …')
        return try_recipe_scrapers(url)

    servings = _parse_yield(node.get('recipeYield'))
    tags = []
    for key in ('keywords', 'recipeCategory', 'recipeCuisine'):
        v = node.get(key, '')
        if isinstance(v, list):
            tags += [str(x).strip() for x in v]
        elif v:
            tags += [x.strip() for x in str(v).split(',')]
    return {
        'name': _strip_html(str(node.get('name', ''))),
        'description': _strip_html(str(node.get('description', ''))),
        'servings': servings,
        'ingredients_raw': [_strip_html(str(i)) for i in node.get('recipeIngredient', [])],
        'instructions': _instructions_text(node.get('recipeInstructions', [])),
        'prep_time': iso_duration_to_min(node.get('prepTime', '')),
        'cook_time': iso_duration_to_min(node.get('cookTime', '')),
        'tags': [t for t in dict.fromkeys(tags) if t][:8],
        'note': f'Quelle: {url}',
    }


def try_recipe_scrapers(url):
    try:
        from recipe_scrapers import scrape_me  # optionale Abhängigkeit
    except ImportError:
        warn('recipe-scrapers ist nicht installiert (pip install recipe-scrapers) — '
             'diese Seite kann nicht gelesen werden')
        return None
    try:
        s = scrape_me(url)
        servings = _parse_yield(s.yields())
        total = None
        try:
            total = s.total_time()
        except Exception:
            pass
        return {
            'name': s.title() or '',
            'description': '',
            'servings': servings,
            'ingredients_raw': list(s.ingredients() or []),
            'instructions': s.instructions() or '',
            'prep_time': f'{total} min' if total else '',
            'cook_time': '',
            'tags': [],
            'note': f'Quelle: {url}',
        }
    except Exception as e:
        warn(f'recipe-scrapers konnte {url} nicht lesen: {e}')
        return None


# ── Quelle 2: Markdown / Text ─────────────────────────────────────
SECTION_ALIASES = {
    'zutaten': 'zutaten', 'ingredients': 'zutaten',
    'zubereitung': 'zubereitung', 'anleitung': 'zubereitung', 'schritte': 'zubereitung',
    'instructions': 'zubereitung', 'directions': 'zubereitung',
    'hinweis': 'hinweis', 'hinweise': 'hinweis', 'tipp': 'hinweis',
    'tipps': 'hinweis', 'notes': 'hinweis',
}


def _section_of(line):
    """Überschrift ('## Zutaten', 'Zutaten:', 'ZUTATEN') → Abschnittsname oder None."""
    l = line.strip().lstrip('#').strip().rstrip(':').strip()
    return SECTION_ALIASES.get(l.casefold())


def recipe_from_textfile(path):
    return recipe_from_text_content(path.read_text(encoding='utf-8-sig', errors='replace'))


def recipe_from_text_content(text):
    lines = text.splitlines()
    r = {'name': '', 'description': '', 'servings': None, 'ingredients_raw': [],
         'instructions': '', 'prep_time': '', 'cook_time': '', 'tags': [], 'note': ''}
    section = None
    body = {'zutaten': [], 'zubereitung': [], 'hinweis': []}
    for line in lines:
        stripped = line.strip()
        sec = _section_of(line)
        if sec:
            section = sec
            continue
        if not r['name'] and stripped.startswith('#'):
            r['name'] = stripped.lstrip('#').strip()
            continue
        low = stripped.casefold()
        m = re.match(r'^portionen\s*[:=]?\s*(\d+)', low) or \
            re.match(r'^personen\s*[:=]?\s*(\d+)', low) or \
            re.search(r'f[üu]r\s+(\d+)\s+(personen|portionen)', low)
        if m and r['servings'] is None:
            r['servings'] = int(m.group(1))
            continue
        if low.startswith('beschreibung:'):
            r['description'] = stripped[13:].strip()
            continue
        if low.startswith('tags:'):
            r['tags'] = [t.strip() for t in stripped[5:].split(',') if t.strip()]
            continue
        if low.startswith('zubereitungszeit:'):
            r['prep_time'] = stripped[17:].strip()
            continue
        if low.startswith('garzeit:'):
            r['cook_time'] = stripped[8:].strip()
            continue
        if section:
            body[section].append(line.rstrip())
        elif not r['name'] and stripped:
            r['name'] = stripped  # erste Textzeile als Titel (txt ohne #)
    r['ingredients_raw'] = [l for l in body['zutaten'] if l.strip()]
    r['instructions'] = '\n'.join(body['zubereitung']).strip()
    r['note'] = '\n'.join(body['hinweis']).strip()
    return r


# ── Ausgabe im App-Importformat ───────────────────────────────────
def _sanitize_field(s):
    """Semikolons würden die Zutaten-Felder trennen — entschärfen."""
    return (s or '').replace(';', ',').replace('\n', ' ').strip()


def _sanitize_text(s):
    """Zeilen, die wie Format-Marker aussehen ('---', '==='), entschärfen."""
    return re.sub(r'(?m)^(---|===)', '—', s or '').strip()


def build_block(r, matcher, default_servings):
    servings = r.get('servings') or default_servings
    if not r.get('servings'):
        warn(f'"{r["name"]}": keine Portionsangabe gefunden — rechne mit {servings} '
             f'(anpassbar über --personen)')
    stats = {'exakt': 0, 'singular': 0, 'fuzzy': 0, 'neu': []}
    ing_lines = []
    for raw in r['ingredients_raw']:
        ing = parse_ingredient_line(raw)
        if not ing:
            continue
        db_name, kind = matcher.match(ing['name'])
        if kind in ('singular', 'fuzzy'):
            info(f'    ↳ Zutat „{ing["name"]}" → „{db_name}" ({kind})')
            stats[kind] += 1
        elif kind == 'exakt':
            stats['exakt'] += 1
        else:
            stats['neu'].append(ing['name'])
        qty_pp = (ing['qty'] or 0) / servings
        fields = [_sanitize_field(db_name), _sanitize_field(ing['prep']),
                  fmt_number(qty_pp), _sanitize_field(ing['unit'])]
        if ing['optional']:
            fields.append('optional')
        ing_lines.append(';'.join(fields))

    out = ['=== REZEPT ===', f'Name: {r["name"]}']
    if r.get('description'):
        out.append(f'Beschreibung: {r["description"]}')
    if r.get('prep_time'):
        out.append(f'Zubereitung: {r["prep_time"]}')
    if r.get('cook_time'):
        out.append(f'Garzeit: {r["cook_time"]}')
    if r.get('tags'):
        out.append(f'Tags: {", ".join(r["tags"])}')
    out.append('--- ZUTATEN')
    out += ing_lines
    if r.get('instructions'):
        out.append('--- ZUBEREITUNG')
        out.append(_sanitize_text(r['instructions']))
    if r.get('note'):
        out.append('--- HINWEIS')
        out.append(_sanitize_text(r['note']))
    out.append('=== ENDE ===')

    info(f'  ✓ „{r["name"]}": {len(ing_lines)} Zutaten für {servings} Personen umgerechnet '
         f'({stats["exakt"]} exakt, {stats["singular"] + stats["fuzzy"]} unscharf zugeordnet, '
         f'{len(stats["neu"])} neu)')
    if stats['neu']:
        warn(f'Neu angelegt werden: {", ".join(stats["neu"])}')
    return '\n'.join(out)


# ── Server-Modus für den „Umwandeln"-Knopf in der App ─────────────
def run_server(port, backup_path):
    import http.server

    class ConvertHandler(http.server.BaseHTTPRequestHandler):
        def _cors(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            # Chrome Private Network Access: erlaubt Zugriff von der
            # GitHub-Pages-Version (https) auf diesen localhost-Server
            self.send_header('Access-Control-Allow-Private-Network', 'true')

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_GET(self):
            # /ping: Erreichbarkeits-Check für den „Umwandeln"-Dialog
            code = 200 if self.path == '/ping' else 404
            body = json.dumps({'ok': code == 200}).encode('utf-8')
            self.send_response(code)
            self._cors()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            global _report
            if self.path != '/convert':
                self.send_response(404)
                self._cors()
                self.end_headers()
                return
            try:
                length = int(self.headers.get('Content-Length', 0))
                data = json.loads(self.rfile.read(length).decode('utf-8'))
            except (ValueError, json.JSONDecodeError):
                data = {}
            _report = []
            try:
                if data.get('url'):
                    r = recipe_from_url(data['url'])
                else:
                    r = recipe_from_text_content(data.get('text', ''))
                # Zutatenliste aus der App (Live-DB) hat Vorrang vor dem Backup
                if data.get('ingredients'):
                    matcher = IngredientMatcher(names=data['ingredients'])
                else:
                    matcher = IngredientMatcher(backup_path)
                if not r or not r.get('name'):
                    resp = {'ok': False, 'error': 'Kein Rezept erkannt', 'report': _report}
                elif not r.get('ingredients_raw'):
                    resp = {'ok': False, 'error': f'"{r["name"]}": keine Zutaten gefunden',
                            'report': _report}
                else:
                    block = build_block(r, matcher, int(data.get('personen') or 4))
                    resp = {'ok': True, 'text': block + '\n', 'report': _report}
            except Exception as e:  # Fehler als JSON zurückgeben statt Absturz
                resp = {'ok': False, 'error': str(e), 'report': _report or []}
            _report = None
            body = json.dumps(resp, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self._cors()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            print(f'  {self.address_string()} — {fmt % args}', file=sys.stderr)

    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), ConvertHandler)
    print(f'Rezept-Konverter läuft auf http://localhost:{port} — in der App: '
          f'Rezeptbuch → ⚡ Umwandeln. Beenden mit Strg+C.', file=sys.stderr)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nBeendet.', file=sys.stderr)
    return 0


def main():
    ap = argparse.ArgumentParser(
        description='Rezepte von Websites/Markdown/Text ins KüFa-Importformat wandeln.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Beispiel:\n  py tools/rezept_import.py https://... rezept.md -o import.txt')
    ap.add_argument('quellen', nargs='*', help='URLs, .md- oder .txt-Dateien')
    ap.add_argument('-o', '--output', default='rezepte_import.txt',
                    help='Ausgabedatei (Standard: rezepte_import.txt)')
    ap.add_argument('--personen', type=int, default=4,
                    help='Portionsannahme, falls die Quelle keine nennt (Standard: 4)')
    ap.add_argument('--backup', default=None,
                    help='Pfad zur standardbackup.json (Standard: neben dem Skript im Repo)')
    ap.add_argument('--server', action='store_true',
                    help='Als lokaler Konverter-Server für den App-Knopf „Umwandeln" laufen')
    ap.add_argument('--port', type=int, default=8124, help='Server-Port (Standard: 8124)')
    args = ap.parse_args()

    backup = Path(args.backup) if args.backup else Path(__file__).resolve().parent.parent / 'standardbackup.json'
    if args.server:
        return run_server(args.port, backup)
    if not args.quellen:
        ap.error('mindestens eine Quelle angeben (oder --server)')
    matcher = IngredientMatcher(backup)

    blocks = []
    for src in args.quellen:
        info(f'Verarbeite {src} …')
        if re.match(r'^https?://', src):
            r = recipe_from_url(src)
        else:
            p = Path(src)
            if not p.exists():
                warn(f'Datei nicht gefunden: {src}')
                continue
            r = recipe_from_textfile(p)
        if not r or not r.get('name'):
            warn(f'Kein Rezept aus {src} extrahiert — übersprungen')
            continue
        if not r.get('ingredients_raw'):
            warn(f'"{r["name"]}": keine Zutaten gefunden — übersprungen')
            continue
        blocks.append(build_block(r, matcher, args.personen))

    if not blocks:
        info('Nichts zu schreiben.')
        return 1
    out_path = Path(args.output)
    out_path.write_text('\n\n'.join(blocks) + '\n', encoding='utf-8')
    info(f'\n{len(blocks)} Rezept(e) → {out_path}')
    info('Bitte kurz prüfen und dann in der App importieren: Rezeptbuch → Import.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
