"""
Парсер данных с сайта lex.uz (ставки пошлин, акцизы, страны)
"""
import re
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class LexUzParser:
    """
    Парсер данных с lex.uz для получения:
    - Ставок импортных пошлин
    - Ставок акцизного налога
    - Списка стран с режимом свободной торговли
    """

    BASE_URL = "https://lex.uz"

    # Known document URLs
    DUTY_RATES_URL = "https://lex.uz/docs/3802366"  # Пошлины
    EXCISE_RATES_URL = "https://lex.uz/docs/6718877"  # Акцизы
    FREE_TRADE_COUNTRIES_URL = "https://lex.uz/docs/4911947"  # Страны свободной торговли
    CERTIFICATION_URL = "https://lex.uz/docs/5249376"  # Сертификация
    UTILIZATION_FEE_URL = "https://lex.uz/docs/4848953"  # Утилизационный сбор

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    async def fetch_page(self, url: str) -> str:
        """Fetch HTML content from URL"""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"Error fetching {url}: {e}")
            raise

    async def parse_duty_rates(self) -> List[Dict]:
        """
        Parse import duty rates from lex.uz

        Returns:
            List of dictionaries with duty rate data:
            {
                'code': '8703231981',
                'description': 'Автомобили...',
                'rate': 30.0,
                'rate_type': 'ad_valorem',  # or 'specific'
                'unit': None,  # or 'USD/кг'
            }
        """
        html = await self.fetch_page(self.DUTY_RATES_URL)
        soup = BeautifulSoup(html, "lxml")

        duty_rates = []

        # Find all tables in the document
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    rate_data = self._parse_duty_row(cells)
                    if rate_data:
                        duty_rates.append(rate_data)

        logger.info(f"Parsed {len(duty_rates)} duty rates from lex.uz")
        return duty_rates

    async def parse_excise_rates(self) -> List[Dict]:
        """
        Parse excise tax rates from lex.uz

        Returns:
            List of dictionaries with excise rate data
        """
        html = await self.fetch_page(self.EXCISE_RATES_URL)
        soup = BeautifulSoup(html, "lxml")

        excise_rates = []
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    rate_data = self._parse_excise_row(cells)
                    if rate_data:
                        excise_rates.append(rate_data)

        logger.info(f"Parsed {len(excise_rates)} excise rates from lex.uz")
        return excise_rates

    async def parse_free_trade_countries(self) -> List[Dict]:
        """
        Parse list of countries with free trade agreements

        Returns:
            List of dictionaries with country data:
            {
                'name': 'Россия',
                'name_en': 'Russia',
                'code': 'RU',
                'is_free_trade': True,
            }
        """
        html = await self.fetch_page(self.FREE_TRADE_COUNTRIES_URL)
        soup = BeautifulSoup(html, "lxml")

        countries = []

        # Look for country names in lists or tables
        # Structure varies, so we try multiple approaches
        lists = soup.find_all(["ul", "ol"])
        for lst in lists:
            items = lst.find_all("li")
            for item in items:
                country_name = item.get_text(strip=True)
                if country_name and len(country_name) > 2:
                    countries.append({
                        "name_ru": country_name,
                        "is_free_trade": True,
                    })

        # Also check tables
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                for cell in cells:
                    text = cell.get_text(strip=True)
                    if text and 3 < len(text) < 50:
                        countries.append({
                            "name_ru": text,
                            "is_free_trade": True,
                        })

        logger.info(f"Parsed {len(countries)} free trade countries from lex.uz")
        return countries

    def _parse_duty_row(self, cells: List) -> Optional[Dict]:
        """Parse a single row of duty rates table"""
        try:
            text_values = [cell.get_text(strip=True) for cell in cells]

            # Look for TN VED code pattern
            code = None
            description = ""
            rate = None
            rate_type = "ad_valorem"
            unit = None

            for i, text in enumerate(text_values):
                # Check for code
                code_match = re.search(r"\d{4,10}", text.replace(" ", ""))
                if code_match and not code:
                    code = code_match.group()
                    continue

                # Check for rate (percentage or specific)
                rate_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
                if rate_match:
                    rate = float(rate_match.group(1).replace(",", "."))
                    rate_type = "ad_valorem"
                    continue

                # Check for specific rate ($/kg, EUR/л, etc.)
                specific_match = re.search(
                    r"(\d+(?:[.,]\d+)?)\s*(USD|EUR|\$|€)?\s*/?\s*(кг|шт|л|литр)",
                    text,
                    re.IGNORECASE
                )
                if specific_match:
                    rate = float(specific_match.group(1).replace(",", "."))
                    rate_type = "specific"
                    unit = specific_match.group(3)
                    continue

                # Otherwise it's likely description
                if len(text) > 10 and not code:
                    description = text

            if code and rate is not None:
                return {
                    "code": code.zfill(10) if len(code) < 10 else code[:10],
                    "description": description,
                    "rate": rate,
                    "rate_type": rate_type,
                    "unit": unit,
                }

        except Exception as e:
            logger.debug(f"Error parsing duty row: {e}")

        return None

    def _parse_excise_row(self, cells: List) -> Optional[Dict]:
        """Parse a single row of excise rates table"""
        try:
            text_values = [cell.get_text(strip=True) for cell in cells]

            code = None
            description = ""
            rate = None
            is_ad_valorem = True
            unit = None

            for text in text_values:
                # Check for code
                code_match = re.search(r"\d{4,10}", text.replace(" ", ""))
                if code_match and not code:
                    code = code_match.group()
                    continue

                # Check for percentage rate
                rate_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
                if rate_match:
                    rate = float(rate_match.group(1).replace(",", "."))
                    is_ad_valorem = True
                    continue

                # Check for specific rate
                specific_match = re.search(
                    r"(\d+(?:[.,]\d+)?)\s*(сум|UZS|USD|\$)",
                    text,
                    re.IGNORECASE
                )
                if specific_match:
                    rate = float(specific_match.group(1).replace(",", "."))
                    is_ad_valorem = False
                    unit = specific_match.group(2)
                    continue

                if len(text) > 10:
                    description = text

            if code and rate is not None:
                return {
                    "code": code.zfill(10) if len(code) < 10 else code[:10],
                    "description": description,
                    "rate": rate,
                    "is_ad_valorem": is_ad_valorem,
                    "unit": unit,
                }

        except Exception as e:
            logger.debug(f"Error parsing excise row: {e}")

        return None

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
