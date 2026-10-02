#!/usr/bin/env python3
"""
Main Entry Point for Lumina Local AI Offline Translator Desktop Application.
Launches the modern CustomTkinter GUI or CLI translation mode.
"""

import sys
import os
import argparse
from pathlib import Path

# Automatically insert project venv site-packages to sys.path if present
_project_root = Path(__file__).parent.resolve()
_venv_site_pkgs = _project_root / "venv" / "Lib" / "site-packages"
if _venv_site_pkgs.exists() and str(_venv_site_pkgs) not in sys.path:
    sys.path.insert(0, str(_venv_site_pkgs))

from core.translator import OfflineTranslator
from ui.app import OfflineTranslatorApp


def main():
    parser = argparse.ArgumentParser(description="Lumina Local AI Offline Translator")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode instead of GUI")
    parser.add_argument("--web", action="store_true", help="Host mobile HTML5 web app accessible from smartphones over Wi-Fi/Hotspot")
    parser.add_argument("--port", type=int, default=5000, help="Port number for mobile web app server (default: 5000)")
    parser.add_argument("--from-lang", type=str, default="auto", help="Source language ISO code (e.g. 'en', 'es', 'auto')")
    parser.add_argument("--to-lang", type=str, default="es", help="Target language ISO code (e.g. 'es', 'fr')")
    parser.add_argument("--text", type=str, help="Text to translate in CLI mode")
    args = parser.parse_args()

    translator = OfflineTranslator()

    if args.web:
        from ui.web_app import start_mobile_web_server
        start_mobile_web_server(translator=translator, port=args.port)
        return

    if args.cli or args.text:
        if not args.text:
            print("Error: --text argument is required in CLI mode.")
            sys.exit(1)
        try:
            res = translator.translate(args.text, args.from_lang, args.to_lang)
            print("\n=== Offline Translation Result ===")
            if res.get("detected"):
                print(f"Detected Source: {res['detected']['name']} ({res['detected']['code']})")
            print(f"Source ({res['source_code']}) -> Target ({res['target_code']})")
            print(f"Output: {res['text']}\n")
        except Exception as e:
            print(f"\nTranslation Failed: {e}\n")
        return

    # Default: Launch GUI application
    app = OfflineTranslatorApp(translator=translator)
    app.mainloop()


if __name__ == "__main__":
    main()
