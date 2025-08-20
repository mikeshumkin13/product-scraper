from __future__ import annotations
from dataclasses import dataclass


@dataclass
class GAProduct:
    """Единица выгрузки «товар Gold Apple».

    Attributes:
        url: Прямая ссылка на карточку товара.
        name: Наименование товара.
        price: Цена в рублях (число в строке без разделителей).
        rating: Рейтинг пользователей (как строка, например "4.7").
        description: Короткое описание (обрезано до лимита).
        instructions: Инструкция по применению (обрезано до лимита).
        country: Страна-производитель (если найдена).
    """

    url: str = ""
    name: str = ""
    price: str = ""
    rating: str = ""
    description: str = ""
    instructions: str = ""
    country: str = ""
