"""
Offline Language Detector Wrapper.
Uses langdetect to detect text language without network access.
"""

import re
from typing import Dict, Any, Optional

try:
    import langdetect
    from langdetect import DetectorFactory
    # Set seed for deterministic detection results across calls
    DetectorFactory.seed = 42
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False


class OfflineLanguageDetector:
    """
    Fast, offline language detection with safe fallback behavior.
    """

    # Comprehensive ISO 639-1 language code to display name mapping
    LANGUAGE_NAMES = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "hi": "Hindi",
        "zh": "Chinese",
        "ja": "Japanese",
        "ar": "Arabic",
        "ru": "Russian",
        "pt": "Portuguese",
        "it": "Italian",
        "nl": "Dutch",
        "ko": "Korean",
        "tr": "Turkish",
        "pl": "Polish",
        "uk": "Ukrainian",
        "vi": "Vietnamese",
        "id": "Indonesian",
        "th": "Thai",
        "cs": "Czech",
        "el": "Greek",
        "he": "Hebrew",
        "sv": "Swedish",
        "da": "Danish",
        "fi": "Finnish",
        "no": "Norwegian",
        "ro": "Romanian",
        "hu": "Hungarian",
        "bn": "Bengali",
        "fa": "Persian",
        "ur": "Urdu",
        "sw": "Swahili",
        "af": "Afrikaans",
        "sq": "Albanian",
        "ca": "Catalan",
        "hr": "Croatian",
        "et": "Estonian",
        "gl": "Galician",
        "gu": "Gujarati",
        "kn": "Kannada",
        "mk": "Macedonian",
        "ml": "Malayalam",
        "mr": "Marathi",
        "ne": "Nepali",
        "pa": "Punjabi",
        "sk": "Slovak",
        "sl": "Slovenian",
        "so": "Somali",
        "tl": "Tagalog",
        "ta": "Tamil",
        "te": "Telugu",
        "cy": "Welsh"
    }

    def __init__(self, default_lang: str = "en"):
        self.default_lang = default_lang

    def get_language_name(self, code: str) -> str:
        """Returns the full human-readable name for a 2-letter ISO code."""
        code_clean = code.lower().strip()
        return self.LANGUAGE_NAMES.get(code_clean, code_clean.upper())

    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detects language of provided text.
        
        Returns:
            Dict containing:
                - code: 2-letter ISO language code (e.g., 'es')
                - name: Full language display name (e.g., 'Spanish')
                - confidence: Float confidence score (0.0 to 1.0)
                - is_reliable: Boolean indicating confidence >= 0.6
        """
        cleaned_text = text.strip()
        
        # Guard clause: empty input or too short
        if not cleaned_text or len(cleaned_text) < 3:
            return {
                "code": self.default_lang,
                "name": self.get_language_name(self.default_lang),
                "confidence": 0.0,
                "is_reliable": False
            }

        # Guard clause: input has no alphabetic characters (only digits/symbols)
        if not re.search(r"[a-zA-Z\u00C0-\u024F\u0400-\u04FF\u0600-\u06FF\u0900-\u097F\u3040-\u30FF\u4E00-\u9FFF]", cleaned_text):
            return {
                "code": self.default_lang,
                "name": self.get_language_name(self.default_lang),
                "confidence": 0.0,
                "is_reliable": False
            }

        if not LANGDETECT_AVAILABLE:
            return {
                "code": self.default_lang,
                "name": self.get_language_name(self.default_lang),
                "confidence": 0.0,
                "is_reliable": False
            }

        try:
            detections = langdetect.detect_langs(cleaned_text)
            if detections:
                top_match = detections[0]
                code = top_match.lang.lower()
                
                # Handle ISO standard differences (e.g. zh-cn -> zh)
                if "-" in code:
                    code = code.split("-")[0]

                prob = float(top_match.prob)
                return {
                    "code": code,
                    "name": self.get_language_name(code),
                    "confidence": prob,
                    "is_reliable": prob >= 0.6
                }
        except Exception:
            pass

        # Fallback if detection fails
        return {
            "code": self.default_lang,
            "name": self.get_language_name(self.default_lang),
            "confidence": 0.0,
            "is_reliable": False
        }
