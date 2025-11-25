"""
Basic internationalization (i18n) layer.
- Players can set a language in their profile or change it live.
- Text keys resolve to localized strings per language.
- Fallback to English when a key or language is missing.

Usage:
    from logic.i18n import Translator
    tr = Translator(lang="en")
    tr.t("tossup_start") -> "Tossup starts!"
"""

from typing import Dict

SUPPORTED_LANGS = {"en", "zh", "de", "fr", "es"}

STRINGS: Dict[str, Dict[str, str]] = {
    "tossup_start": {
        "en": "Tossup starts!",
        "zh": "抢答开始！",
        "de": "Eröffnungsfrage beginnt!",
        "fr": "Question à réponse directe commence !",
        "es": "¡Comienza la pregunta de respuesta rápida!"
    },
    "buzz_locked": {
        "en": "Buzz locked by",
        "zh": "抢答锁定：",
        "de": "Buzz gesperrt von",
        "fr": "Buzzer verrouillé par",
        "es": "Zumbador bloqueado por"
    },
    "correct": {
        "en": "Correct",
        "zh": "正确",
        "de": "Richtig",
        "fr": "Correct",
        "es": "Correcto"
    },
    "incorrect": {
        "en": "Incorrect",
        "zh": "错误",
        "de": "Falsch",
        "fr": "Incorrect",
        "es": "Incorrecto"
    },
    "sudden_death": {
        "en": "Sudden-death tossup begins!",
        "zh": "突然死亡抢答开始！",
        "de": "Sudden-Death-Frage beginnt!",
        "fr": "Question en mort subite commence !",
        "es": "¡Comienza la pregunta de muerte súbita!"
    },
    "timer_label": {
        "en": "Time remaining",
        "zh": "剩余时间",
        "de": "Verbleibende Zeit",
        "fr": "Temps restant",
        "es": "Tiempo restante"
    }
}

class Translator:
    def __init__(self, lang: str = "en"):
        self.lang = lang if lang in SUPPORTED_LANGS else "en"

    def set_language(self, lang: str):
        self.lang = lang if lang in SUPPORTED_LANGS else "en"

    def t(self, key: str) -> str:
        bundle = STRINGS.get(key, {})
        return bundle.get(self.lang, bundle.get("en", key))