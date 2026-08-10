#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Startet den KüFa Organizer komplett:
  - App-Server (statisch) auf http://localhost:8123
  - Rezept-Konverter für den „⚡ Umwandeln"-Knopf auf http://localhost:8124
  - öffnet den Browser

Aufruf:  py tools/start.py  [--no-browser]  [--port 8123]  [--conv-port 8124]
Bequemer: start.bat im Repo-Ordner doppelklicken. Beenden mit Strg+C.

Läuft einer der beiden Server bereits (Port belegt), wird er übersprungen —
das Skript kann also auch nachträglich nur den fehlenden Teil starten.
"""
import argparse
import functools
import http.server
import socket
import sys
import threading
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rezept_import  # noqa: E402  (Konverter mit --server-Logik)

ROOT = Path(__file__).resolve().parent.parent
print = functools.partial(print, flush=True)  # Meldungen sofort anzeigen (auch umgeleitet)

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass


def port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) != 0


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # App-Requests nicht in die Konsole spammen


def main():
    ap = argparse.ArgumentParser(description='KüFa Organizer starten (App + Rezept-Konverter).')
    ap.add_argument('--port', type=int, default=8123, help='App-Port (Standard: 8123)')
    ap.add_argument('--conv-port', type=int, default=8124, help='Konverter-Port (Standard: 8124)')
    ap.add_argument('--no-browser', action='store_true', help='Browser nicht automatisch öffnen')
    args = ap.parse_args()

    threads = []

    if port_free(args.port):
        handler = functools.partial(QuietHandler, directory=str(ROOT))
        app_srv = http.server.ThreadingHTTPServer(('127.0.0.1', args.port), handler)
        threads.append(threading.Thread(target=app_srv.serve_forever, daemon=True))
        print(f'✓ App-Server: http://localhost:{args.port}')
    else:
        print(f'• Port {args.port} ist schon belegt — App-Server läuft vermutlich bereits.')

    conv_running = not port_free(args.conv_port)
    if conv_running:
        print(f'• Port {args.conv_port} ist schon belegt — Konverter läuft vermutlich bereits.')

    for th in threads:
        th.start()

    if not args.no_browser:
        webbrowser.open(f'http://localhost:{args.port}')

    if conv_running:
        if not threads:
            print('Nichts zu tun — beide Server laufen schon.')
            return 0
        print('Beenden mit Strg+C.')
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            print('\nBeendet.')
        return 0

    # Konverter blockierend im Hauptthread (übernimmt Strg+C-Behandlung)
    backup = ROOT / 'standardbackup.json'
    return rezept_import.run_server(args.conv_port, backup)


if __name__ == '__main__':
    sys.exit(main())
