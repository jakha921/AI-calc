"""
Парсер курсов валют от Центрального банка Узбекистана (cbu.uz)
"""
import httpx
from datetime import date, datetime
from typing import List, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class CurrencyParser:
    """Парсер курсов валют от ЦБ Узбекистана"""

    BASE_URL = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"

    # Main currencies we need
    MAIN_CURRENCIES = ["USD", "EUR", "RUB", "CNY", "GBP", "JPY", "KRW", "TRY"]

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_rates(self, rate_date: Optional[date] = None) -> List[dict]:
        """
        Fetch currency rates from CBU API

        Args:
            rate_date: Date for rates (default: today)

        Returns:
            List of currency rate dictionaries
        """
        if rate_date is None:
            rate_date = date.today()

        url = f"{self.BASE_URL}"

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            rates = []
            for item in data:
                currency_data = {
                    "code": item.get("Ccy", ""),
                    "ccy": item.get("Ccy", ""),
                    "name": item.get("CcyNm_EN", ""),
                    "name_ru": item.get("CcyNm_RU", ""),
                    "rate": float(item.get("Rate", 0)),
                    "nominal": int(item.get("Nominal", 1)),
                    "rate_date": rate_date,
                    "diff": item.get("Diff", "0"),
                }
                rates.append(currency_data)

            logger.info(f"Fetched {len(rates)} currency rates from CBU")
            return rates

        except httpx.HTTPError as e:
            logger.error(f"Error fetching currency rates: {e}")
            raise

    async def fetch_main_currencies(self, rate_date: Optional[date] = None) -> List[dict]:
        """Fetch only main currencies"""
        all_rates = await self.fetch_rates(rate_date)
        return [r for r in all_rates if r["code"] in self.MAIN_CURRENCIES]

    async def get_usd_rate(self, rate_date: Optional[date] = None) -> float:
        """Get USD to UZS rate"""
        rates = await self.fetch_rates(rate_date)
        for rate in rates:
            if rate["code"] == "USD":
                return rate["rate"]
        raise ValueError("USD rate not found")

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
