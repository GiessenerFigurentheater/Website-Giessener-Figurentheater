#!/usr/bin/env python3
"""Lokale Vorschau der fertigen Website (Ordner _site/) unter http://localhost:8765.

Anders als `python3 -m http.server` verbietet dieser Server dem Browser das Zwischenspeichern,
damit nach jedem `python3 build.py` sofort die neue Fassung angezeigt wird.
Aufruf: python3 vorschau.py
"""
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ORDNER = Path(__file__).parent / "_site"


class OhneCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    handler = functools.partial(OhneCache, directory=str(ORDNER))
    print("Vorschau läuft unter http://localhost:8765 – beenden mit Strg+C")
    ThreadingHTTPServer(("", 8765), handler).serve_forever()
