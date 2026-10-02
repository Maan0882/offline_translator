#!/usr/bin/env python3
"""
One-Time Model Downloader for Offline Translator.
Run this script while connected to the internet to fetch and install language pairs.
After downloading, the translator functions 100% offline.
"""

import argparse
import sys
import os
import shutil
import tempfile
from pathlib import Path
from typing import List

# Automatically insert project venv site-packages to sys.path if present
_project_root = Path(__file__).parent.resolve()
_venv_site_pkgs = _project_root / "venv" / "Lib" / "site-packages"
if _venv_site_pkgs.exists() and str(_venv_site_pkgs) not in sys.path:
    sys.path.insert(0, str(_venv_site_pkgs))

# Force UTF-8 encoding on standard output for Windows console compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

try:
    import argostranslate.package
    import argostranslate.translate
except ImportError:
    print("ERROR: argostranslate is not installed.")
    print("Please install dependencies using: pip install -r requirements.txt")
    sys.exit(1)


DEFAULT_PAIRS = [
    "en-es", "es-en",  # English <-> Spanish
    "en-fr", "fr-en",  # English <-> French
    "en-de", "de-en",  # English <-> German
    "en-hi", "hi-en",  # English <-> Hindi
    "en-zh", "zh-en",  # English <-> Chinese
    "en-it", "it-en",  # English <-> Italian
    "en-ja", "ja-en",  # English <-> Japanese
    "en-ru", "ru-en",  # English <-> Russian
    "en-ar", "ar-en",  # English <-> Arabic
    "en-pt", "pt-en",  # English <-> Portuguese
]


def list_models():
    """Lists online available models and locally installed models."""
    print("Fetching package index from Argos Translate repository...")
    try:
        argostranslate.package.update_package_index()
    except Exception as e:
        print(f"Warning: Could not fetch online index (Check internet connection): {e}")

    installed = argostranslate.translate.get_installed_languages()
    installed_codes = {lang.code for lang in installed}
    print(f"\n[+] Currently Installed Languages ({len(installed)}):")
    for lang in installed:
        print(f"  - {lang.name} ({lang.code})")

    try:
        available_packages = argostranslate.package.get_available_packages()
        print(f"\n[+] Available Online Translation Packages ({len(available_packages)}):")
        for pkg in available_packages:
            is_installed = any(
                p.from_code == pkg.from_code and p.to_code == pkg.to_code
                for p in argostranslate.package.get_installed_packages()
            )
            status = "[INSTALLED]" if is_installed else "[AVAILABLE]"
            print(f"  - {pkg.from_name} ({pkg.from_code}) -> {pkg.to_name} ({pkg.to_code}) {status}")
    except Exception as e:
        print(f"Could not load online package list: {e}")


def download_and_install_pairs(pairs: List[str]):
    """Downloads and installs specified language pair packages."""
    print("Updating Argos Translate package index...")
    try:
        argostranslate.package.update_package_index()
    except Exception as e:
        print(f"ERROR: Failed to download package index. Internet connection required for model setup.\nDetails: {e}")
        sys.exit(1)

    available_packages = argostranslate.package.get_available_packages()
    installed_packages = argostranslate.package.get_installed_packages()

    installed_pair_keys = {(pkg.from_code, pkg.to_code) for pkg in installed_packages}

    # Normalize requested pairs
    target_pairs = set()
    for item in pairs:
        for p in item.split(","):
            p_clean = p.strip().lower()
            if "-" in p_clean:
                target_pairs.add(tuple(p_clean.split("-")[:2]))
            else:
                print(f"Warning: Ignoring invalid pair format '{p}'. Use format 'from-to' (e.g. en-es)")

    if not target_pairs:
        print("No valid target language pairs requested.")
        return

    print(f"\nPreparing to process {len(target_pairs)} language pairs...")

    temp_dir = tempfile.mkdtemp(prefix="argos_download_")

    try:
        for from_code, to_code in target_pairs:
            pair_str = f"{from_code}->{to_code}"

            if (from_code, to_code) in installed_pair_keys:
                print(f"✔️ Pair {pair_str} is already installed. Skipping.")
                continue

            # Find package in available packages
            pkg_to_download = next(
                (pkg for pkg in available_packages if pkg.from_code == from_code and pkg.to_code == to_code),
                None
            )

            if not pkg_to_download:
                print(f"❌ Pair {pair_str} is NOT available in Argos package repository.")
                continue

            print(f"\n[↓] Downloading model for {pkg_to_download.from_name} -> {pkg_to_download.to_name}...")
            
            download_path = pkg_to_download.download()
            
            print(f"[↑] Installing package: {pkg_to_download.from_name} -> {pkg_to_download.to_name}...")
            argostranslate.package.install_from_path(download_path)
            
            # Clean up individual download file if saved to temp
            if os.path.exists(download_path):
                try:
                    os.remove(download_path)
                except Exception:
                    pass

            print(f"✅ Successfully installed {pair_str}!")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("🎉 MODEL SETUP COMPLETE!")
    print("Installed Languages:")
    for lang in argostranslate.translate.get_installed_languages():
        print(f"  • {lang.name} ({lang.code})")
    print("You can now run the application completely OFFLINE using:")
    print("  python main.py")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="One-time model downloade for Offline Python Translator.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--pairs",
        type=str,
        help="Comma-separated language pairs to download (e.g. 'en-es,es-en,en-fr,fr-en')"
    )
    parser.add_argument(
        "--default",
        action="store_true",
        help="Download standard recommended language pairs (English <-> Spanish, French, German, Hindi, Chinese, etc.)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download ALL available language pairs from repository (Requires ~5-10GB space)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available online models and installed local models"
    )

    args = parser.parse_args()

    if args.list:
        list_models()
        return

    if args.all:
        try:
            argostranslate.package.update_package_index()
            pkgs = argostranslate.package.get_available_packages()
            pairs = [f"{p.from_code}-{p.to_code}" for p in pkgs]
            download_and_install_pairs(pairs)
        except Exception as e:
            print(f"Error fetching all packages: {e}")
        return

    if args.pairs:
        pairs = args.pairs.split(",")
        download_and_install_pairs(pairs)
        return

    # Default fallback behavior if no flags provided or --default passed
    print("Downloading default language pairs (English, Spanish, French, German, Hindi, Chinese, Japanese, Russian, Arabic, Portuguese)...")
    download_and_install_pairs(DEFAULT_PAIRS)


if __name__ == "__main__":
    main()
