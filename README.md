# 🌐 Lumina AI — Local Offline Neural Translator

A fully functional, 100% local, privacy-first offline translator that runs entirely on your laptop without any internet connection after initial model setup.

Powered by **Argos Translate** (CTranslate2 open-source NMT framework), **langdetect** for offline language identification, and **CustomTkinter** for a sleek, modern desktop user interface.

---

## ✨ Key Features

- **100% Offline Runtime**: Zero network requests or API calls during translation.
- **Neural Machine Translation (NMT)**: Powered by quantized `int8` CPU models for fast performance on standard laptops.
- **Google Translate UI**: Dual-pane layout, auto-detect source language, character count, live debounced translation, clear, copy, paste, and language swap capabilities.
- **Language Auto-Detection**: Fast offline language detection with fallback.
- **Thread-Safe LRU Cache**: Avoids re-translating identical phrases and provides near-instant cached responses.
- **Pivot Translation Routing**: Translates directly between pairs or automatically pivots through English if direct models are missing.
- **Dark & Light Mode**: Toggle UI theme with a single click.

---

## 📁 Project Structure

```
offline_translator/
├── requirements.txt         # Dependency constraints
├── download_models.py       # One-time script to fetch NMT package weights online
├── core/
│   ├── __init__.py
│   ├── translator.py        # Translation engine wrapper, pivot routing, & LRU cache
│   └── detector.py          # Offline language detection wrapper
├── ui/
│   ├── __init__.py
│   └── app.py               # CustomTkinter GUI layout & debounced event handlers
├── main.py                  # Application entry point (GUI / CLI)
└── README.md                # Documentation & packaging guide
```

---

## 🚀 Step 1: Installation & Setup

### Prerequisites
- Python 3.9+ (Python 3.10, 3.11, 3.12, 3.13, 3.14 supported)
- Internet connection **only during initial setup** to download model weights.

### 1. Create Virtual Environment
Open your terminal inside the project directory:

```bash
# Windows (PowerShell / CMD)
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 📥 Step 2: One-Time Model Setup (`download_models.py`)

Run `download_models.py` **while connected to Wi-Fi/Ethernet** to download target language packages onto your machine.

### Quick Start (Recommended Default Models)
Downloads popular language pairs: English ↔ Spanish, French, German, Hindi, Chinese, Italian, Japanese, Russian, Arabic, Portuguese.

```bash
python download_models.py --default
```

### Custom Language Pairs
Specify exact language pairs using the `--pairs` flag:

```bash
python download_models.py --pairs en-es,es-en,en-fr,fr-en,en-hi,hi-en
```

### List Online & Installed Models
```bash
python download_models.py --list
```

### Download All Available Pairs
```bash
python download_models.py --all
```

---

## 🔌 Step 3: Run 100% Disconnected (Offline Verification)

1. Turn off your laptop's Wi-Fi / disconnect Ethernet.
2. Launch the application:

```bash
python main.py
```

### CLI Mode (Optional)
You can also run instant translations directly from your command line:

```bash
python main.py --cli --from-lang auto --to-lang es --text "Hello world, this runs offline!"
```

---

## 📦 Step 4: Standalone Executable Packaging Guide

To bundle this application into a standalone desktop `.exe` (or executable on macOS/Linux) that can run on computers without Python installed:

### 1. Install PyInstaller
```bash
pip install pyinstaller
```

### 2. Bundle App using PyInstaller

Run the following command to bundle into a single folder executable:

```bash
pyinstaller --noconfirm --onedir --windowed --name "OfflineTranslator" --collect-all customtkinter --collect-all argostranslate --collect-all stanza --collect-all ctranslate2 main.py
```

- The compiled executable will be located in: `dist/OfflineTranslator/OfflineTranslator.exe`
- You can distribute the `dist/OfflineTranslator` directory or create an installer (using Inno Setup or NSIS).

---

## 🛠️ Troubleshooting & FAQ

- **Missing Language Pair Error**: If the UI shows "No translation package found", run `python download_models.py --pairs <source>-<target>` online to install the model package or ensure English (`en`) pivot packages are installed.
- **CPU Speed**: Argos Translate runs on CTranslate2 int8 quantized models, which are optimized for standard CPU execution. Typical translation latency is 10–60ms per phrase.

---

## 📜 License
MIT License. Free for personal and commercial offline translation use.
