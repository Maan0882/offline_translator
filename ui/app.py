"""
Desktop User Interface for Lumina Local AI Translator.
Modern, intuitive, 100% offline desktop application with thread-safe debounced live translation,
quick language chips, dark/light theme switching, and instant clipboard actions.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, List

import customtkinter as ctk

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

from core.translator import OfflineTranslator, TranslationError


# Configure CustomTkinter Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class OfflineTranslatorApp(ctk.CTk):
    """
    Main Desktop GUI Application Window for Lumina Local AI Translator.
    """

    def __init__(self, translator: Optional[OfflineTranslator] = None):
        super().__init__()

        self.translator = translator if translator else OfflineTranslator()
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Application Window Configuration
        self.title("Lumina AI - Local Offline Neural Translator")
        self.geometry("1160 x 740")
        self.minsize(960, 620)

        # State Variables
        self.debounce_timer: Optional[str] = None
        self.is_translating = False
        self.last_detected_name = ""
        self.appearance_mode = "Dark"

        # Language Registry Data
        self.installed_langs: List[Dict[str, str]] = []
        self.lang_name_to_code: Dict[str, str] = {}
        self.lang_code_to_name: Dict[str, str] = {}

        self._refresh_language_registry()

        # Build UI Components
        self._build_header()
        self._build_workspace()
        self._build_status_bar()

        # Bind window close event
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _refresh_language_registry(self):
        """Fetches installed language packages from OfflineTranslator core."""
        self.installed_langs = self.translator.get_available_languages()
        self.lang_name_to_code = {item["name"]: item["code"] for item in self.installed_langs}
        self.lang_code_to_name = {item["code"]: item["name"] for item in self.installed_langs}

    def _build_header(self):
        """Constructs top header bar with modern branding, privacy badge, theme toggle, and reload button."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=55)
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        # Left Branding Block
        brand_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        brand_box.pack(side="left")

        logo_title = ctk.CTkLabel(
            brand_box,
            text="Lumina AI",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=("#1a73e8", "#38bdf8")
        )
        logo_title.pack(side="left")

        sub_title = ctk.CTkLabel(
            brand_box,
            text="Local Offline Translator",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            text_color=("gray40", "gray70")
        )
        sub_title.pack(side="left", padx=(8, 12))

        # Security / Privacy Badge
        privacy_badge = ctk.CTkLabel(
            brand_box,
            text="🔒 100% On-Device & Private",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=("#e6f4ea", "#064e3b"),
            text_color=("#137333", "#34d399"),
            corner_radius=8,
            padx=10,
            pady=4
        )
        privacy_badge.pack(side="left", padx=5)

        # Right Controls (Refresh Models + Theme Switch)
        controls_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_box.pack(side="right")

        self.refresh_btn = ctk.CTkButton(
            controls_box,
            text="🔄 Refresh Models",
            width=130,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray85", "#27272a"),
            hover_color=("gray75", "#3f3f46"),
            text_color=("black", "white"),
            command=self._on_click_refresh_models
        )
        self.refresh_btn.pack(side="left", padx=8)

        self.theme_switch = ctk.CTkSwitch(
            controls_box,
            text="Dark Mode",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle_theme
        )
        self.theme_switch.select()
        self.theme_switch.pack(side="left", padx=8)

    def _build_workspace(self):
        """Constructs modern two-card workspace layout."""
        self.workspace = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace.pack(fill="both", expand=True, padx=20, pady=5)

        self.workspace.columnconfigure(0, weight=1)
        self.workspace.columnconfigure(1, weight=0)
        self.workspace.columnconfigure(2, weight=1)
        self.workspace.rowconfigure(0, weight=1)

        # ==========================================
        # LEFT CARD: SOURCE INPUT & LANGUAGE CHIPS
        # ==========================================
        self.left_card = ctk.CTkFrame(
            self.workspace,
            corner_radius=14,
            border_width=1,
            border_color=("gray80", "#3f3f46"),
            fg_color=("gray95", "#18181b")
        )
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=5)

        # Left Card Header (Dropdown + Quick Chips)
        left_header = ctk.CTkFrame(self.left_card, fg_color="transparent")
        left_header.pack(fill="x", padx=15, pady=(12, 5))

        src_title = ctk.CTkLabel(
            left_header,
            text="FROM:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray"
        )
        src_title.pack(side="left", padx=(0, 8))

        source_dropdown_values = ["Auto-detect"] + [l["name"] for l in self.installed_langs]
        self.source_dropdown = ctk.CTkOptionMenu(
            left_header,
            values=source_dropdown_values,
            font=ctk.CTkFont(size=13, weight="bold"),
            dropdown_font=ctk.CTkFont(size=12),
            width=165,
            command=self._on_source_lang_changed
        )
        self.source_dropdown.set("Auto-detect")
        self.source_dropdown.pack(side="left")

        # Auto-detect Feedback Badge
        self.detected_tag = ctk.CTkLabel(
            left_header,
            text="",
            font=ctk.CTkFont(size=11, weight="bold", slant="italic"),
            text_color=("#1a73e8", "#38bdf8")
        )
        self.detected_tag.pack(side="left", padx=10)

        # Quick Language Selection Chips (Left)
        self.left_chips_frame = ctk.CTkFrame(self.left_card, fg_color="transparent")
        self.left_chips_frame.pack(fill="x", padx=15, pady=(2, 6))
        self._build_quick_chips(self.left_chips_frame, is_source=True)

        # Input Textbox Area
        self.input_textbox = ctk.CTkTextbox(
            self.left_card,
            font=ctk.CTkFont(family="Segoe UI", size=15),
            wrap="word",
            undo=True,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "#27272a")
        )
        self.input_textbox.pack(fill="both", expand=True, padx=15, pady=5)
        self.input_textbox.bind("<KeyRelease>", self._on_input_key_release)

        # Left Card Footer (Toolbar)
        left_footer = ctk.CTkFrame(self.left_card, fg_color="transparent", height=40)
        left_footer.pack(fill="x", padx=15, pady=(5, 12))

        self.btn_clear = ctk.CTkButton(
            left_footer,
            text="🗑️ Clear Text",
            width=90,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color=("gray80", "#3f3f46"),
            hover_color=("gray85", "#27272a"),
            text_color=("gray20", "gray80"),
            command=self._on_click_clear
        )
        self.btn_clear.pack(side="left", padx=(0, 6))

        self.btn_paste = ctk.CTkButton(
            left_footer,
            text="📋 Paste Clipboard",
            width=115,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color=("gray80", "#3f3f46"),
            hover_color=("gray85", "#27272a"),
            text_color=("gray20", "gray80"),
            command=self._on_click_paste
        )
        self.btn_paste.pack(side="left")

        self.char_count_label = ctk.CTkLabel(
            left_footer,
            text="0 / 5000 chars",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.char_count_label.pack(side="right")

        # ==========================================
        # CENTER ACTION CONTROL COLUMN
        # ==========================================
        center_card = ctk.CTkFrame(self.workspace, fg_color="transparent")
        center_card.grid(row=0, column=1, sticky="ns", padx=6, pady=5)

        self.btn_swap = ctk.CTkButton(
            center_card,
            text="⇆",
            width=44,
            height=44,
            corner_radius=22,
            font=ctk.CTkFont(size=22, weight="bold"),
            fg_color=("#1a73e8", "#2563eb"),
            hover_color=("#1557b0", "#1d4ed8"),
            command=self._on_click_swap
        )
        self.btn_swap.pack(expand=True, pady=(0, 30))

        self.btn_translate_now = ctk.CTkButton(
            center_card,
            text="⚡ Translate",
            width=100,
            height=38,
            corner_radius=10,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray85", "#27272a"),
            hover_color=("gray75", "#3f3f46"),
            text_color=("black", "white"),
            command=self._trigger_translation
        )
        self.btn_translate_now.pack(expand=True, pady=(0, 40))

        # ==========================================
        # RIGHT CARD: TARGET OUTPUT & LANGUAGE CHIPS
        # ==========================================
        self.right_card = ctk.CTkFrame(
            self.workspace,
            corner_radius=14,
            border_width=1,
            border_color=("gray80", "#3f3f46"),
            fg_color=("gray95", "#18181b")
        )
        self.right_card.grid(row=0, column=2, sticky="nsew", padx=(6, 0), pady=5)

        # Right Card Header
        right_header = ctk.CTkFrame(self.right_card, fg_color="transparent")
        right_header.pack(fill="x", padx=15, pady=(12, 5))

        tgt_title = ctk.CTkLabel(
            right_header,
            text="TO:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray"
        )
        tgt_title.pack(side="left", padx=(0, 8))

        target_dropdown_values = [l["name"] for l in self.installed_langs] if self.installed_langs else ["English"]
        self.target_dropdown = ctk.CTkOptionMenu(
            right_header,
            values=target_dropdown_values,
            font=ctk.CTkFont(size=13, weight="bold"),
            dropdown_font=ctk.CTkFont(size=12),
            width=165,
            command=self._on_target_lang_changed
        )

        default_target = "English" if "English" in target_dropdown_values else (target_dropdown_values[0] if target_dropdown_values else "")
        self.target_dropdown.set(default_target)
        self.target_dropdown.pack(side="left")

        self.cache_indicator = ctk.CTkLabel(
            right_header,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#1e8e3e", "#34d399")
        )
        self.cache_indicator.pack(side="right")

        # Quick Language Selection Chips (Right)
        self.right_chips_frame = ctk.CTkFrame(self.right_card, fg_color="transparent")
        self.right_chips_frame.pack(fill="x", padx=15, pady=(2, 6))
        self._build_quick_chips(self.right_chips_frame, is_source=False)

        # Output Textbox Area
        self.output_textbox = ctk.CTkTextbox(
            self.right_card,
            font=ctk.CTkFont(family="Segoe UI", size=15),
            wrap="word",
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "#27272a")
        )
        self.output_textbox.pack(fill="both", expand=True, padx=15, pady=5)

        # Right Card Footer (Toolbar)
        right_footer = ctk.CTkFrame(self.right_card, fg_color="transparent", height=40)
        right_footer.pack(fill="x", padx=15, pady=(5, 12))

        self.btn_copy = ctk.CTkButton(
            right_footer,
            text="📋 Copy Translation",
            width=145,
            height=32,
            corner_radius=8,
            fg_color=("#1a73e8", "#2563eb"),
            hover_color=("#1557b0", "#1d4ed8"),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_click_copy_output
        )
        self.btn_copy.pack(side="left")

        self.output_stats_label = ctk.CTkLabel(
            right_footer,
            text="0 words",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.output_stats_label.pack(side="right")

    def _build_quick_chips(self, parent_frame: ctk.CTkFrame, is_source: bool):
        """Constructs 1-click quick language selection buttons (chips)."""
        # Clear existing children if any
        for widget in parent_frame.winfo_children():
            widget.destroy()

        available_chips = []
        if is_source:
            available_chips.append("Auto-detect")

        # Pick top installed languages for chips
        for lang in self.installed_langs:
            if lang["name"] not in available_chips and len(available_chips) < 6:
                available_chips.append(lang["name"])

        for name in available_chips:
            chip_btn = ctk.CTkButton(
                parent_frame,
                text=name,
                height=24,
                corner_radius=12,
                font=ctk.CTkFont(size=11),
                fg_color=("gray88", "#27272a"),
                hover_color=("gray80", "#3f3f46"),
                text_color=("gray15", "gray85"),
                command=lambda n=name, src=is_source: self._on_chip_clicked(n, src)
            )
            chip_btn.pack(side="left", padx=2)

    def _on_chip_clicked(self, name: str, is_source: bool):
        """Callback when a quick language chip is clicked."""
        if is_source:
            self.source_dropdown.set(name)
            self._on_source_lang_changed(name)
        else:
            self.target_dropdown.set(name)
            self._on_target_lang_changed(name)

    def _build_status_bar(self):
        """Constructs bottom status bar for engine info and offline stats."""
        self.status_bar = ctk.CTkFrame(self, height=32, corner_radius=0, fg_color=("gray90", "#111827"))
        self.status_bar.pack(fill="x", side="bottom")

        installed_count = len(self.installed_langs)
        initial_status = (
            f"🔒 100% Offline Mode Active | Installed Languages: {installed_count} | Engine: Argos / CTranslate2 (int8 CPU Quantized)"
            if installed_count > 0
            else "⚠️ No language models found! Run 'python download_models.py' to download language packages."
        )

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text=initial_status,
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray70")
        )
        self.status_label.pack(side="left", padx=15, pady=4)

    # ==========================================
    # EVENT HANDLERS & DEBOUNCED TRANSLATION
    # ==========================================

    def _on_input_key_release(self, event=None):
        """Handles live debounced translation when user types into the input box."""
        text = self.input_textbox.get("1.0", "end-1c")
        char_count = len(text)
        self.char_count_label.configure(text=f"{char_count} / 5000 chars")

        if self.debounce_timer:
            self.after_cancel(self.debounce_timer)

        self.debounce_timer = self.after(350, self._trigger_translation)

    def _trigger_translation(self):
        """Starts translation execution in background thread worker."""
        text = self.input_textbox.get("1.0", "end-1c").strip()

        if not text:
            self.output_textbox.delete("1.0", "end")
            self.detected_tag.configure(text="")
            self.cache_indicator.configure(text="")
            self.output_stats_label.configure(text="0 words")
            return

        if not self.installed_langs:
            self.status_label.configure(
                text="⚠️ Cannot translate: No local models installed. Run 'python download_models.py' while online."
            )
            return

        src_name = self.source_dropdown.get()
        tgt_name = self.target_dropdown.get()

        src_code = "auto" if src_name == "Auto-detect" else self.lang_name_to_code.get(src_name, "en")
        tgt_code = self.lang_name_to_code.get(tgt_name, "en")

        self.status_label.configure(text=f"⏳ Translating {len(text)} characters offline...")
        self.cache_indicator.configure(text="⏳ Translating...")
        self.is_translating = True

        self.executor.submit(self._async_translate_task, text, src_code, tgt_code)

    def _async_translate_task(self, text: str, src_code: str, tgt_code: str):
        """Background thread execution body."""
        start_time = time.time()
        try:
            result = self.translator.translate(text, src_code, tgt_code)
            elapsed_ms = int((time.time() - start_time) * 1000)
            result["elapsed_ms"] = elapsed_ms
            self.after(0, self._update_translation_ui, result, None)
        except Exception as err:
            self.after(0, self._update_translation_ui, None, str(err))

    def _update_translation_ui(self, result: Optional[Dict], error_msg: Optional[str]):
        """Main thread callback to update output text area and status indicators."""
        self.is_translating = False

        if error_msg:
            self.output_textbox.delete("1.0", "end")
            self.output_textbox.insert("1.0", f"Error: {error_msg}")
            self.status_label.configure(text=f"Translation Error: {error_msg}")
            self.detected_tag.configure(text="")
            self.cache_indicator.configure(text="")
            return

        if not result:
            return

        translated_text = result.get("text", "")
        self.output_textbox.delete("1.0", "end")
        self.output_textbox.insert("1.0", translated_text)

        words = len(translated_text.split()) if translated_text else 0
        self.output_stats_label.configure(text=f"{words} words")

        detected = result.get("detected")
        if detected and self.source_dropdown.get() == "Auto-detect":
            det_name = detected.get("name", "Unknown")
            det_code = detected.get("code", "")
            self.last_detected_name = det_name
            self.detected_tag.configure(text=f"Detected: {det_name} ({det_code})")
        else:
            self.detected_tag.configure(text="")

        if result.get("cache_hit"):
            self.cache_indicator.configure(text="⚡ Instant Cache")
        else:
            elapsed = result.get("elapsed_ms", 0)
            self.cache_indicator.configure(text=f"⚙️ {elapsed}ms")

        hit_count = self.translator.cache.hits
        self.status_label.configure(
            text=f"🔒 Offline Mode Active | Installed Models: {len(self.installed_langs)} | Cache Hits: {hit_count} | Latency: {result.get('elapsed_ms', 0)}ms"
        )

    def _on_click_swap(self):
        """Swaps source and target language selections and input/output texts."""
        src_val = self.source_dropdown.get()
        tgt_val = self.target_dropdown.get()

        if src_val == "Auto-detect":
            src_val = getattr(self, "last_detected_name", "") or "English"

        self.source_dropdown.set(tgt_val)
        self.target_dropdown.set(src_val)

        in_text = self.input_textbox.get("1.0", "end-1c")
        out_text = self.output_textbox.get("1.0", "end-1c")

        self.input_textbox.delete("1.0", "end")
        self.input_textbox.insert("1.0", out_text)

        self._on_input_key_release()

    def _on_source_lang_changed(self, choice: str):
        self._trigger_translation()

    def _on_target_lang_changed(self, choice: str):
        self._trigger_translation()

    def _on_click_clear(self):
        self.input_textbox.delete("1.0", "end")
        self.output_textbox.delete("1.0", "end")
        self.char_count_label.configure(text="0 / 5000 chars")
        self.output_stats_label.configure(text="0 words")
        self.detected_tag.configure(text="")
        self.cache_indicator.configure(text="")

    def _on_click_paste(self):
        if PYPERCLIP_AVAILABLE:
            try:
                clip_text = pyperclip.paste()
                if clip_text:
                    self.input_textbox.delete("1.0", "end")
                    self.input_textbox.insert("1.0", clip_text)
                    self._on_input_key_release()
            except Exception:
                pass

    def _on_click_copy_output(self):
        out_text = self.output_textbox.get("1.0", "end-1c").strip()
        if out_text and PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(out_text)
                self.btn_copy.configure(text="✅ Copied to Clipboard!", fg_color=("#1e8e3e", "#10b981"))
                self.after(1500, lambda: self.btn_copy.configure(
                    text="📋 Copy Translation",
                    fg_color=("#1a73e8", "#2563eb")
                ))
            except Exception:
                pass

    def _on_click_refresh_models(self):
        """Rescans offline model packages and updates dropdown lists dynamically."""
        self._refresh_language_registry()

        src_values = ["Auto-detect"] + [l["name"] for l in self.installed_langs]
        tgt_values = [l["name"] for l in self.installed_langs]

        self.source_dropdown.configure(values=src_values)
        if tgt_values:
            self.target_dropdown.configure(values=tgt_values)

        self._build_quick_chips(self.left_chips_frame, is_source=True)
        self._build_quick_chips(self.right_chips_frame, is_source=False)

        self.status_label.configure(
            text=f"Refreshed offline models! Installed languages: {len(self.installed_langs)}"
        )

    def _toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
            self.appearance_mode = "Dark"
        else:
            ctk.set_appearance_mode("Light")
            self.appearance_mode = "Light"

    def _on_close(self):
        self.executor.shutdown(wait=False)
        self.destroy()
