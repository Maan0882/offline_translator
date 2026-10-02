"""
Desktop User Interface for Offline Google Translate Clone.
Built using CustomTkinter with thread-safe debounced live translation,
dark/light theme switching, model management status, and copy features.
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
    Main Desktop GUI Application Window for Google Translate Offline.
    """

    def __init__(self, translator: Optional[OfflineTranslator] = None):
        super().__init__()

        self.translator = translator if translator else OfflineTranslator()
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Application Window Configuration
        self.title("Google Translate - Offline AI")
        self.geometry("1120 x 700")
        self.minsize(920, 580)

        # State Variables
        self.debounce_timer: Optional[str] = None
        self.translation_counter = 0
        self.is_translating = False
        self.last_translated_text = ""
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

        # Bind events
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _refresh_language_registry(self):
        """Fetches installed language packages from OfflineTranslator core."""
        self.installed_langs = self.translator.get_available_languages()
        self.lang_name_to_code = {item["name"]: item["code"] for item in self.installed_langs}
        self.lang_code_to_name = {item["code"]: item["name"] for item in self.installed_langs}

    def _build_header(self):
        """Constructs top header bar with branding, status badge, theme toggle, and reload button."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        # Brand / Title Block
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        app_title = ctk.CTkLabel(
            title_box,
            text="Google Translate",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=("#1a73e8", "#4285f4")
        )
        app_title.pack(side="left")

        offline_badge = ctk.CTkLabel(
            title_box,
            text="OFFLINE MODE",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color=("#e6f4ea", "#137333"),
            text_color=("#137333", "#e6f4ea"),
            corner_radius=6
        )
        offline_badge.pack(side="left", padx=12, pady=4)

        # Right Controls (Theme Switch + Refresh Button)
        controls_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_box.pack(side="right")

        self.refresh_btn = ctk.CTkButton(
            controls_box,
            text="🔄 Refresh Models",
            width=120,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"),
            text_color=("black", "white"),
            command=self._on_click_refresh_models
        )
        self.refresh_btn.pack(side="left", padx=8)

        self.theme_switch = ctk.CTkSwitch(
            controls_box,
            text="Dark Mode",
            font=ctk.CTkFont(size=12),
            command=self._toggle_theme
        )
        self.theme_switch.select()
        self.theme_switch.pack(side="left", padx=8)

    def _build_workspace(self):
        """Constructs the two-column Google Translate split card layout."""
        self.workspace = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace.pack(fill="both", expand=True, padx=20, pady=5)

        self.workspace.columnconfigure(0, weight=1)
        self.workspace.columnconfigure(1, weight=0)
        self.workspace.columnconfigure(2, weight=1)
        self.workspace.rowconfigure(0, weight=1)

        # ==========================================
        # LEFT PANE: SOURCE LANGUAGE & INPUT TEXT
        # ==========================================
        self.left_card = ctk.CTkFrame(self.workspace, corner_radius=12)
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=5)

        # Left Card Header (Language Selector)
        left_header = ctk.CTkFrame(self.left_card, fg_color="transparent", height=45)
        left_header.pack(fill="x", padx=15, pady=(12, 5))

        source_label = ctk.CTkLabel(
            left_header,
            text="Source:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray"
        )
        source_label.pack(side="left", padx=(0, 5))

        source_dropdown_values = ["Auto-detect"] + [l["name"] for l in self.installed_langs]
        self.source_dropdown = ctk.CTkOptionMenu(
            left_header,
            values=source_dropdown_values,
            font=ctk.CTkFont(size=13, weight="bold"),
            dropdown_font=ctk.CTkFont(size=12),
            width=170,
            command=self._on_source_lang_changed
        )
        self.source_dropdown.set("Auto-detect")
        self.source_dropdown.pack(side="left")

        # Auto-detect feedback tag
        self.detected_tag = ctk.CTkLabel(
            left_header,
            text="",
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color=("#1a73e8", "#8ab4f8")
        )
        self.detected_tag.pack(side="left", padx=10)

        # Left Input Textbox
        self.input_textbox = ctk.CTkTextbox(
            self.left_card,
            font=ctk.CTkFont(family="Segoe UI", size=15),
            wrap="word",
            undo=True,
            corner_radius=8
        )
        self.input_textbox.pack(fill="both", expand=True, padx=15, pady=5)
        self.input_textbox.bind("<KeyRelease>", self._on_input_key_release)

        # Left Card Bottom Toolbar
        left_footer = ctk.CTkFrame(self.left_card, fg_color="transparent", height=40)
        left_footer.pack(fill="x", padx=15, pady=(5, 12))

        self.btn_clear = ctk.CTkButton(
            left_footer,
            text="🗑️ Clear",
            width=70,
            height=30,
            fg_color="transparent",
            hover_color=("gray85", "gray30"),
            text_color=("gray20", "gray80"),
            command=self._on_click_clear
        )
        self.btn_clear.pack(side="left", padx=(0, 5))

        self.btn_paste = ctk.CTkButton(
            left_footer,
            text="📋 Paste",
            width=70,
            height=30,
            fg_color="transparent",
            hover_color=("gray85", "gray30"),
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
        # CENTER COLUMN: SWAP & MANUAL ACTION BUTTON
        # ==========================================
        center_card = ctk.CTkFrame(self.workspace, fg_color="transparent")
        center_card.grid(row=0, column=1, sticky="ns", padx=4, pady=5)

        self.btn_swap = ctk.CTkButton(
            center_card,
            text="⇆",
            width=42,
            height=42,
            corner_radius=21,
            font=ctk.CTkFont(size=20, weight="bold"),
            fg_color=("#1a73e8", "#4285f4"),
            hover_color=("#1557b0", "#1a73e8"),
            command=self._on_click_swap
        )
        self.btn_swap.pack(expand=True, pady=(0, 40))

        self.btn_translate_now = ctk.CTkButton(
            center_card,
            text="Translate",
            width=90,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40"),
            text_color=("black", "white"),
            command=self._trigger_translation
        )
        self.btn_translate_now.pack(expand=True, pady=(0, 50))

        # ==========================================
        # RIGHT PANE: TARGET LANGUAGE & OUTPUT TEXT
        # ==========================================
        self.right_card = ctk.CTkFrame(self.workspace, corner_radius=12)
        self.right_card.grid(row=0, column=2, sticky="nsew", padx=(6, 0), pady=5)

        # Right Card Header (Language Selector)
        right_header = ctk.CTkFrame(self.right_card, fg_color="transparent", height=45)
        right_header.pack(fill="x", padx=15, pady=(12, 5))

        target_label = ctk.CTkLabel(
            right_header,
            text="Target:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray"
        )
        target_label.pack(side="left", padx=(0, 5))

        target_dropdown_values = [l["name"] for l in self.installed_langs] if self.installed_langs else ["Spanish"]
        self.target_dropdown = ctk.CTkOptionMenu(
            right_header,
            values=target_dropdown_values,
            font=ctk.CTkFont(size=13, weight="bold"),
            dropdown_font=ctk.CTkFont(size=12),
            width=170,
            command=self._on_target_lang_changed
        )
        
        # Default target language selection
        default_target = "Spanish" if "Spanish" in target_dropdown_values else (target_dropdown_values[0] if target_dropdown_values else "")
        self.target_dropdown.set(default_target)
        self.target_dropdown.pack(side="left")

        self.cache_indicator = ctk.CTkLabel(
            right_header,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#1e8e3e", "#34a853")
        )
        self.cache_indicator.pack(side="right")

        # Right Output Textbox
        self.output_textbox = ctk.CTkTextbox(
            self.right_card,
            font=ctk.CTkFont(family="Segoe UI", size=15),
            wrap="word",
            corner_radius=8
        )
        self.output_textbox.pack(fill="both", expand=True, padx=15, pady=5)

        # Right Card Bottom Toolbar
        right_footer = ctk.CTkFrame(self.right_card, fg_color="transparent", height=40)
        right_footer.pack(fill="x", padx=15, pady=(5, 12))

        self.btn_copy = ctk.CTkButton(
            right_footer,
            text="📋 Copy Translation",
            width=140,
            height=30,
            fg_color=("#1a73e8", "#4285f4"),
            hover_color=("#1557b0", "#1a73e8"),
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

    def _build_status_bar(self):
        """Constructs bottom status bar for engine info and warnings."""
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color=("gray90", "gray18"))
        self.status_bar.pack(fill="x", side="bottom")

        installed_count = len(self.installed_langs)
        initial_status = f"Ready | Installed Languages: {installed_count} | CPU int8 Engine" if installed_count > 0 else "⚠️ No language models found! Run 'python download_models.py' to download language packages."

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text=initial_status,
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray70")
        )
        self.status_label.pack(side="left", padx=15, pady=3)

    # ==========================================
    # EVENT HANDLERS & DEBOUNCED LIVE TRANSLATION
    # ==========================================

    def _on_input_key_release(self, event=None):
        """Handles live debounced translation when user types into the input box."""
        text = self.input_textbox.get("1.0", "end-1c")
        char_count = len(text)
        self.char_count_label.configure(text=f"{char_count} / 5000 chars")

        # Cancel existing pending timer if user keeps typing
        if self.debounce_timer:
            self.after_cancel(self.debounce_timer)

        # Schedule live translation after 350ms pause
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
                text="⚠️ Cannot translate: No local models installed. Run 'python download_models.py' while connected to internet."
            )
            return

        src_name = self.source_dropdown.get()
        tgt_name = self.target_dropdown.get()

        src_code = "auto" if src_name == "Auto-detect" else self.lang_name_to_code.get(src_name, "en")
        tgt_code = self.lang_name_to_code.get(tgt_name, "es")

        self.status_label.configure(text=f"⏳ Translating {len(text)} characters offline...")
        self.cache_indicator.configure(text="⏳ Translating...")
        self.is_translating = True

        # Dispatch task to thread pool
        self.executor.submit(self._async_translate_task, text, src_code, tgt_code)

    def _async_translate_task(self, text: str, src_code: str, tgt_code: str):
        """Background thread execution body."""
        start_time = time.time()
        try:
            result = self.translator.translate(text, src_code, tgt_code)
            elapsed_ms = int((time.time() - start_time) * 1000)
            result["elapsed_ms"] = elapsed_ms
            # Thread-safe UI update back on main thread
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

        # Update word count
        words = len(translated_text.split()) if translated_text else 0
        self.output_stats_label.configure(text=f"{words} words")

        # Update Auto-detect feedback tag
        detected = result.get("detected")
        if detected and self.source_dropdown.get() == "Auto-detect":
            det_name = detected.get("name", "Unknown")
            det_code = detected.get("code", "")
            self.last_detected_name = det_name
            self.detected_tag.configure(text=f"Detected: {det_name} ({det_code})")
        else:
            self.detected_tag.configure(text="")

        # Cache indicator
        if result.get("cache_hit"):
            self.cache_indicator.configure(text="⚡ Cached")
        else:
            elapsed = result.get("elapsed_ms", 0)
            self.cache_indicator.configure(text=f"⚙️ {elapsed}ms")

        hit_count = self.translator.cache.hits
        self.status_label.configure(
            text=f"Ready | Installed: {len(self.installed_langs)} | Cache Hits: {hit_count} | Latency: {result.get('elapsed_ms', 0)}ms"
        )

    def _on_click_swap(self):
        """Swaps source and target language selections and input/output texts."""
        src_val = self.source_dropdown.get()
        tgt_val = self.target_dropdown.get()

        if src_val == "Auto-detect":
            # If auto-detect was selected, resolve what was detected or fallback to English
            src_val = "English"

        # Swap dropdown values
        self.source_dropdown.set(tgt_val)
        self.target_dropdown.set(src_val)

        # Swap text contents
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
                # Visual temporary feedback
                self.btn_copy.configure(text="✅ Copied!", fg_color=("#1e8e3e", "#34a853"))
                self.after(1500, lambda: self.btn_copy.configure(
                    text="📋 Copy Translation",
                    fg_color=("#1a73e8", "#4285f4")
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
