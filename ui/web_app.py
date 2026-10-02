"""
Mobile Web Application Server for Lumina Local AI Translator.
Provides a modern, responsive HTML5 mobile app accessible from any smartphone,
tablet, or browser over local Wi-Fi / Hotspot without internet access.
"""

import socket
import logging
from flask import Flask, request, jsonify, render_template_string
from core.translator import OfflineTranslator

logger = logging.getLogger(__name__)


def get_local_ip() -> str:
    """Returns local network IP address of the host machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


MOBILE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Lumina AI — Mobile Offline Translator</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --card-border: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-hover: #0284c7;
            --success-green: #34d399;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 12px;
            display: flex;
            flex-direction: column;
        }

        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 4px 16px 4px;
        }

        .brand-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: var(--accent-blue);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .badge-offline {
            background-color: rgba(52, 211, 153, 0.15);
            color: var(--success-green);
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 8px;
            border-radius: 6px;
            border: 1px solid rgba(52, 211, 153, 0.3);
        }

        .app-container {
            display: flex;
            flex-direction: column;
            gap: 12px;
            flex: 1;
        }

        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        select {
            background-color: #0f172a;
            color: var(--text-primary);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 0.95rem;
            font-weight: 700;
            outline: none;
            width: 100%;
            max-width: 180px;
        }

        .chip-container {
            display: flex;
            gap: 6px;
            overflow-x: auto;
            padding-bottom: 4px;
            -webkit-overflow-scrolling: touch;
        }

        .chip {
            background-color: #0f172a;
            color: var(--text-secondary);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 4px 10px;
            font-size: 0.75rem;
            white-space: nowrap;
            cursor: pointer;
        }

        textarea {
            width: 100%;
            height: 120px;
            background-color: #0f172a;
            color: var(--text-primary);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 10px;
            font-size: 1rem;
            line-height: 1.4;
            resize: none;
            outline: none;
        }

        .output-box {
            width: 100%;
            min-height: 120px;
            background-color: #0f172a;
            color: var(--text-primary);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 10px;
            font-size: 1rem;
            line-height: 1.4;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .action-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .btn {
            background-color: #0f172a;
            color: var(--text-primary);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 8px 14px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .btn-primary {
            background-color: #0284c7;
            color: white;
            border: none;
            justify-content: center;
            padding: 12px;
            font-size: 1rem;
            border-radius: 10px;
            font-weight: 700;
        }

        .swap-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: -4px 0;
        }

        .btn-swap {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            background-color: #0284c7;
            color: white;
            border: none;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 10px rgba(2, 132, 199, 0.4);
        }

        footer {
            margin-top: 16px;
            text-align: center;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <header>
        <div class="brand-title">
            <span>⚡ Lumina Mobile AI</span>
        </div>
        <div class="badge-offline">🔒 100% Offline</div>
    </header>

    <div class="app-container">
        <!-- Input Card -->
        <div class="card">
            <div class="card-header">
                <span style="font-size:0.75rem; font-weight:800; color:var(--text-secondary);">FROM:</span>
                <select id="sourceLang" onchange="onLangChange()">
                    <option value="auto">Auto-detect</option>
                </select>
            </div>
            <div class="chip-container" id="sourceChips"></div>
            <textarea id="inputText" placeholder="Type or paste text to translate..." oninput="onInputDebounce()"></textarea>
            <div class="action-row">
                <button class="btn" onclick="clearInput()">🗑️ Clear</button>
                <span id="charCount">0 / 5000 chars</span>
            </div>
        </div>

        <!-- Swap Control -->
        <div class="swap-container">
            <button class="btn-swap" onclick="swapLanguages()">⇆</button>
        </div>

        <!-- Output Card -->
        <div class="card">
            <div class="card-header">
                <span style="font-size:0.75rem; font-weight:800; color:var(--text-secondary);">TO:</span>
                <select id="targetLang" onchange="onLangChange()"></select>
            </div>
            <div class="chip-container" id="targetChips"></div>
            <div class="output-box" id="outputText">Translated text will appear here...</div>
            <div class="action-row">
                <button class="btn" id="copyBtn" onclick="copyOutput()">📋 Copy</button>
                <span id="outputStats">0 words</span>
            </div>
        </div>

        <button class="btn btn-primary" onclick="triggerTranslation()">⚡ Translate Now</button>
    </div>

    <footer>
        🔒 On-Device NMT Engine • Argos/CTranslate2 (int8 Quantized)
    </footer>

    <script>
        let installedLangs = [];
        let debounceTimer = null;

        async function init() {
            try {
                const res = await fetch('/api/languages');
                installedLangs = await res.json();
                populateDropdowns();
            } catch (err) {
                console.error("Error loading languages:", err);
            }
        }

        function populateDropdowns() {
            const srcSel = document.getElementById('sourceLang');
            const tgtSel = document.getElementById('targetLang');
            const srcChips = document.getElementById('sourceChips');
            const tgtChips = document.getElementById('targetChips');

            srcSel.innerHTML = '<option value="auto">Auto-detect</option>';
            tgtSel.innerHTML = '';
            srcChips.innerHTML = '<div class="chip" onclick="setLang(\'source\', \'auto\')">Auto</div>';
            tgtChips.innerHTML = '';

            installedLangs.forEach(lang => {
                const opt1 = document.createElement('option');
                opt1.value = lang.code;
                opt1.textContent = lang.name;
                srcSel.appendChild(opt1);

                const opt2 = document.createElement('option');
                opt2.value = lang.code;
                opt2.textContent = lang.name;
                tgtSel.appendChild(opt2);

                const chip1 = document.createElement('div');
                chip1.className = 'chip';
                chip1.textContent = lang.name;
                chip1.onclick = () => setLang('source', lang.code);
                srcChips.appendChild(chip1);

                const chip2 = document.createElement('div');
                chip2.className = 'chip';
                chip2.textContent = lang.name;
                chip2.onclick = () => setLang('target', lang.code);
                tgtChips.appendChild(chip2);
            });

            if (installedLangs.length > 0) {
                tgtSel.value = installedLangs[0].code;
            }
        }

        function setLang(type, code) {
            if (type === 'source') {
                document.getElementById('sourceLang').value = code;
            } else {
                document.getElementById('targetLang').value = code;
            }
            triggerTranslation();
        }

        function onInputDebounce() {
            const text = document.getElementById('inputText').value;
            document.getElementById('charCount').textContent = `${text.length} / 5000 chars`;
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(triggerTranslation, 400);
        }

        function onLangChange() {
            triggerTranslation();
        }

        async function triggerTranslation() {
            const text = document.getElementById('inputText').value.trim();
            const srcCode = document.getElementById('sourceLang').value;
            const tgtCode = document.getElementById('targetLang').value;
            const outBox = document.getElementById('outputText');

            if (!text) {
                outBox.textContent = "Translated text will appear here...";
                document.getElementById('outputStats').textContent = "0 words";
                return;
            }

            outBox.textContent = "⏳ Translating offline...";

            try {
                const res = await fetch('/api/translate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text, from_lang: srcCode, to_lang: tgtCode})
                });

                const data = await res.json();
                if (data.error) {
                    outBox.textContent = "Error: " + data.error;
                } else {
                    outBox.textContent = data.text;
                    const words = data.text ? data.text.split(/\\s+/).length : 0;
                    document.getElementById('outputStats').textContent = `${words} words`;
                }
            } catch (err) {
                outBox.textContent = "Translation failed: " + err;
            }
        }

        function swapLanguages() {
            const srcSel = document.getElementById('sourceLang');
            const tgtSel = document.getElementById('targetLang');
            const inText = document.getElementById('inputText');
            const outBox = document.getElementById('outputText');

            const tempLang = srcSel.value === 'auto' ? 'en' : srcSel.value;
            srcSel.value = tgtSel.value;
            tgtSel.value = tempLang;

            if (outBox.textContent && !outBox.textContent.startsWith("⏳") && !outBox.textContent.startsWith("Translated text")) {
                inText.value = outBox.textContent;
            }
            triggerTranslation();
        }

        function clearInput() {
            document.getElementById('inputText').value = '';
            document.getElementById('outputText').textContent = 'Translated text will appear here...';
            document.getElementById('charCount').textContent = '0 / 5000 chars';
            document.getElementById('outputStats').textContent = '0 words';
        }

        function copyOutput() {
            const text = document.getElementById('outputText').textContent;
            if (text && !text.startsWith("⏳") && !text.startsWith("Translated text")) {
                navigator.clipboard.writeText(text);
                const btn = document.getElementById('copyBtn');
                btn.textContent = "✅ Copied!";
                setTimeout(() => btn.textContent = "📋 Copy", 1500);
            }
        }

        window.onload = init;
    </script>
</body>
</html>
"""


def start_mobile_web_server(translator: OfflineTranslator, port: int = 5000):
    """Launches Flask web application server for mobile phones."""
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(MOBILE_HTML_TEMPLATE)

    @app.route("/api/languages", methods=["GET"])
    def get_languages():
        langs = translator.get_available_languages()
        return jsonify(langs)

    @app.route("/api/translate", methods=["POST"])
    def translate():
        data = request.json or {}
        text = data.get("text", "").strip()
        from_lang = data.get("from_lang", "auto")
        to_lang = data.get("to_lang", "en")

        if not text:
            return jsonify({"text": "", "detected": None})

        try:
            res = translator.translate(text, from_lang, to_lang)
            return jsonify(res)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    local_ip = get_local_ip()
    print("\n" + "=" * 65)
    print("📱 LUMINA MOBILE AI OFFLINE TRANSLATOR SERVER IS RUNNING!")
    print("Connect your smartphone (iPhone / Android) to the same Wi-Fi / Hotspot.")
    print(f"Open this URL on your mobile phone browser:\n")
    print(f"    👉  http://{local_ip}:{port}")
    print("=" * 65 + "\n")

    app.run(host="0.0.0.0", port=port, debug=False)
