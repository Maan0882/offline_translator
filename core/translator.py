"""
Offline Translator Service Wrapper.
Manages argostranslate models, language registries, translation execution,
pivot routing, and thread-safe caching.
"""

import logging
from collections import OrderedDict
import threading
from typing import List, Dict, Any, Tuple, Optional

from .detector import OfflineLanguageDetector

logger = logging.getLogger(__name__)

try:
    import argostranslate.package
    import argostranslate.translate
    ARGOS_AVAILABLE = True
except ImportError:
    ARGOS_AVAILABLE = False


class ThreadSafeLRUCache:
    """Thread-safe LRU cache for storing translation results."""

    def __init__(self, capacity: int = 512):
        self.capacity = capacity
        self.cache: OrderedDict[Tuple[str, str, str], str] = OrderedDict()
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: Tuple[str, str, str]) -> Optional[str]:
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            self.misses += 1
            return None

    def put(self, key: Tuple[str, str, str], value: str) -> None:
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def clear(self) -> None:
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0


class TranslationError(Exception):
    """Custom exception raised when translation fails or model pair is missing."""
    pass


class OfflineTranslator:
    """
    Offline Machine Translation Engine.
    Uses local Argos Translate models for zero-network execution.
    """

    def __init__(self, cache_size: int = 512):
        self.detector = OfflineLanguageDetector()
        self.cache = ThreadSafeLRUCache(capacity=cache_size)
        self._installed_languages: List[Dict[str, str]] = []
        self._language_map: Dict[str, Any] = {}
        self.reload_installed_languages()

    def reload_installed_languages(self) -> List[Dict[str, str]]:
        """
        Scans local storage for installed Argos Translate packages and returns language list.
        """
        if not ARGOS_AVAILABLE:
            self._installed_languages = []
            self._language_map = {}
            return []

        try:
            installed = argostranslate.translate.get_installed_languages()
            self._language_map = {lang.code: lang for lang in installed}
            
            result = []
            for lang in installed:
                name = self.detector.get_language_name(lang.code)
                # If argostranslate returns native name, keep standard display name
                if hasattr(lang, "name") and lang.name and lang.name != lang.code:
                    name = lang.name.capitalize()
                
                result.append({
                    "code": lang.code,
                    "name": name
                })

            # Sort alphabetically by language name
            result.sort(key=lambda x: x["name"])
            self._installed_languages = result
            return self._installed_languages
        except Exception as e:
            logger.error(f"Error scanning installed models: {e}")
            self._installed_languages = []
            self._language_map = {}
            return []

    def get_available_languages(self) -> List[Dict[str, str]]:
        """Returns the list of currently installed languages."""
        if not self._installed_languages:
            self.reload_installed_languages()
        return self._installed_languages

    def is_pair_available(self, from_code: str, to_code: str) -> bool:
        """Checks if translation model path exists between source and target language."""
        if from_code == to_code:
            return True
        
        from_lang = self._language_map.get(from_code)
        to_lang = self._language_map.get(to_code)
        
        if not from_lang or not to_lang:
            return False

        # Direct pair check
        translation = from_lang.get_translation(to_lang)
        if translation is not None:
            return True

        # Check pivot routing via English ('en')
        if from_code != "en" and to_code != "en":
            en_lang = self._language_map.get("en")
            if en_lang:
                t1 = from_lang.get_translation(en_lang)
                t2 = en_lang.get_translation(to_lang)
                if t1 is not None and t2 is not None:
                    return True

        return False

    def translate(self, text: str, from_lang: str, to_lang: str) -> Dict[str, Any]:
        """
        Translates text offline from source language to target language.

        Args:
            text: Input text string
            from_lang: Source ISO code or 'auto'/'Auto-detect'
            to_lang: Target ISO code

        Returns:
            Dict containing:
                - text: Translated output text
                - source_code: Resolved source language code
                - target_code: Target language code
                - detected: Info dict if auto-detection was used
                - cache_hit: True if result was returned from LRU cache
        """
        if not text or not text.strip():
            return {
                "text": "",
                "source_code": from_lang,
                "target_code": to_lang,
                "detected": None,
                "cache_hit": False
            }

        if not ARGOS_AVAILABLE:
            raise TranslationError("Argos Translate engine is not installed. Please install requirements.txt.")

        raw_input = text.strip()
        detected_info = None
        actual_from = from_lang.lower().strip()
        actual_to = to_lang.lower().strip()

        # Handle Auto-Detect
        if actual_from in ["auto", "auto-detect", "autodetect"]:
            detected_info = self.detector.detect_language(raw_input)
            actual_from = detected_info["code"]

        # If source and target are identical, return as is
        if actual_from == actual_to:
            return {
                "text": raw_input,
                "source_code": actual_from,
                "target_code": actual_to,
                "detected": detected_info,
                "cache_hit": False
            }

        # Check cache
        cache_key = (raw_input, actual_from, actual_to)
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return {
                "text": cached_result,
                "source_code": actual_from,
                "target_code": actual_to,
                "detected": detected_info,
                "cache_hit": True
            }

        # Resolve installed language objects
        src_obj = self._language_map.get(actual_from)
        tgt_obj = self._language_map.get(actual_to)

        if not src_obj or not tgt_obj:
            missing_code = actual_from if not src_obj else actual_to
            missing_name = self.detector.get_language_name(missing_code)
            available_names = [l["name"] for l in self._installed_languages]
            raise TranslationError(
                f"Missing installed model for '{missing_name}' ({missing_code}). "
                f"Installed: {available_names}. "
                f"To install, run: python download_models.py --pairs en-{missing_code},{missing_code}-en"
            )

        # Attempt Direct Translation
        translation = src_obj.get_translation(tgt_obj)
        translated_output = ""

        if translation is not None:
            translated_output = translation.translate(raw_input)
        else:
            # Attempt Pivot Translation via English
            if actual_from != "en" and actual_to != "en":
                en_obj = self._language_map.get("en")
                if en_obj:
                    t1 = src_obj.get_translation(en_obj)
                    t2 = en_obj.get_translation(tgt_obj)
                    if t1 is not None and t2 is not None:
                        intermediate = t1.translate(raw_input)
                        translated_output = t2.translate(intermediate)

        if not translated_output:
            src_name = self.detector.get_language_name(actual_from)
            tgt_name = self.detector.get_language_name(actual_to)
            raise TranslationError(
                f"No translation package found for pair {src_name} ({actual_from}) -> {tgt_name} ({actual_to}). "
                f"To install, run: python download_models.py --pairs {actual_from}-{actual_to}"
            )

        # Sanitize any infinite token repetition loops from model output
        translated_output = self._clean_repeated_hallucinations(translated_output)

        # Cache result
        self.cache.put(cache_key, translated_output)

        return {
            "text": translated_output,
            "source_code": actual_from,
            "target_code": actual_to,
            "detected": detected_info,
            "cache_hit": False
        }

    def _clean_repeated_hallucinations(self, text: str) -> str:
        """Detects and truncates infinite repetition loops from NMT model outputs."""
        if not text:
            return text
        import re
        pattern = r'(.{2,50}?)\1{3,}'
        match = re.search(pattern, text)
        if match:
            cleaned = text[:match.start() + len(match.group(1))].strip()
            return cleaned.rstrip(" ,.-;:?!")
        return text
