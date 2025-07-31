from abc import ABC, abstractmethod
from typing import List, Dict


class BaseParser(ABC):
    @abstractmethod
    def fetch_page(self, url: str) -> str:
        """Загружает HTML страницу"""
        pass

    @abstractmethod
    def parse(self, html: str) -> List[Dict]:
        """Парсит HTML и возвращает список товаров"""
        pass

    def run(self, url: str) -> List[Dict]:
        html = self.fetch_page(url)
        return self.parse(html)


