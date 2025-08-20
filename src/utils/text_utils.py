"""Утилиты для нормализации и обрезки текстов."""

from __future__ import annotations
import re
from typing import Optional


def clean_text(s: str) -> str:
    """Нормализует пробелы/переводы строк и обрезает крайние пробелы."""
    if not s:
        return ""
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)  # множественные пробелы/табы → один пробел
    s = re.sub(r"[ \t]+\n", "\n", s)  # УБИРАЕМ ТОЛЬКО ПРОБЕЛЫ/ТАБЫ перед \n,
    s = re.sub(r"\n{3,}", "\n\n", s)  # 3+ переводов строки → 2 перевода
    s = re.sub(r"\n[ \t]+", "\n", s)  # ПРОБЕЛЫ ПОСЛЕ \n
    return s.strip()


def shorten_text(s: str, limit: Optional[int]) -> str:
    """Обрезает текст до ``limit`` символов по границе предложения/слова.

    Если удаётся — заканчивает на . ! ?  иначе режет по последнему пробелу.
    Возвращает исходный текст, если ``limit`` не задан.
    """
    if not s or not limit:
        return s or ""
    s = clean_text(s)
    if len(s) <= limit:
        return s
    m = re.search(rf"^(.{{0,{limit}}}[.!?])\s", s)
    if m and len(m.group(1)) >= int(limit * 0.6):
        return m.group(1).strip() + "…"
    cut = s[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.strip() + "…"


def digits(text: str) -> str:
    """Извлекает только цифры из строки (например, из '7 104 ₽' → '7104')."""
    return "".join(ch for ch in (text or "") if ch.isdigit())
