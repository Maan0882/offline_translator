"""
Core package for Offline Translator.
Provides translation engine wrappers, language detection, and model management.
"""

from .translator import OfflineTranslator
from .detector import OfflineLanguageDetector

__all__ = ["OfflineTranslator", "OfflineLanguageDetector"]
