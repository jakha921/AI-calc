"""
Сервис для работы с курсами валют
"""
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from app.models.currency import Currency
from app.parsers.currency_parser import CurrencyParser
from app.schemas.currency import CurrencySchema, CurrencyRatesResponse

logger = logging.getLogger(__name__)


class CurrencyService:
    """Сервис для получения и обновления курсов валют"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.parser = CurrencyParser()

    async def get_rate(self, currency_code: str, rate_date: Optional[date] = None) -> Optional[float]:
        """
        Get exchange rate for a currency

        Args:
            currency_code: Currency code (USD, EUR, etc.)
            rate_date: Date for the rate (default: today)

        Returns:
            Exchange rate to UZS or None if not found
        """
        if rate_date is None:
            rate_date = date.today()

        # Try to get from database first
        result = await self.db.execute(
            select(Currency).where(
                and_(
                    Currency.code == currency_code.upper(),
                    Currency.rate_date == rate_date
                )
            )
        )
        currency = result.scalar_one_or_none()

        if currency:
            return currency.rate_per_unit

        # If not in DB, fetch from API and save
        try:
            await self.update_rates(rate_date)
            result = await self.db.execute(
                select(Currency).where(
                    and_(
                        Currency.code == currency_code.upper(),
                        Currency.rate_date == rate_date
                    )
                )
            )
            currency = result.scalar_one_or_none()
            if currency:
                return currency.rate_per_unit
        except Exception as e:
            logger.error(f"Error fetching rate for {currency_code}: {e}")

        # Fallback: get latest available rate
        result = await self.db.execute(
            select(Currency)
            .where(Currency.code == currency_code.upper())
            .order_by(Currency.rate_date.desc())
            .limit(1)
        )
        currency = result.scalar_one_or_none()
        return currency.rate_per_unit if currency else None

    async def get_all_rates(self, rate_date: Optional[date] = None) -> CurrencyRatesResponse:
        """Get all currency rates for a date"""
        if rate_date is None:
            rate_date = date.today()

        result = await self.db.execute(
            select(Currency).where(Currency.rate_date == rate_date)
        )
        currencies = result.scalars().all()

        if not currencies:
            # Fetch from API
            await self.update_rates(rate_date)
            result = await self.db.execute(
                select(Currency).where(Currency.rate_date == rate_date)
            )
            currencies = result.scalars().all()

        return CurrencyRatesResponse(
            rates=[CurrencySchema.model_validate(c) for c in currencies],
            date=rate_date,
            source="cbu.uz"
        )

    async def update_rates(self, rate_date: Optional[date] = None) -> int:
        """
        Update currency rates from CBU API

        Args:
            rate_date: Date for rates (default: today)

        Returns:
            Number of rates updated
        """
        if rate_date is None:
            rate_date = date.today()

        try:
            async with CurrencyParser() as parser:
                rates_data = await parser.fetch_rates(rate_date)

                count = 0
                for rate_info in rates_data:
                    # Check if already exists
                    result = await self.db.execute(
                        select(Currency).where(
                            and_(
                                Currency.code == rate_info["code"],
                                Currency.rate_date == rate_date
                            )
                        )
                    )
                    existing = result.scalar_one_or_none()

                    if existing:
                        # Update existing
                        existing.rate = rate_info["rate"]
                        existing.nominal = rate_info["nominal"]
                        existing.updated_at = datetime.utcnow()
                    else:
                        # Create new
                        currency = Currency(
                            code=rate_info["code"],
                            ccy=rate_info.get("ccy"),
                            name=rate_info["name"],
                            name_ru=rate_info.get("name_ru"),
                            rate=rate_info["rate"],
                            nominal=rate_info["nominal"],
                            rate_date=rate_date,
                        )
                        self.db.add(currency)
                    count += 1

                await self.db.commit()
                logger.info(f"Updated {count} currency rates for {rate_date}")
                return count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating currency rates: {e}")
            raise

    async def get_usd_rate(self, rate_date: Optional[date] = None) -> float:
        """Get USD to UZS rate"""
        rate = await self.get_rate("USD", rate_date)
        if rate is None:
            raise ValueError("USD rate not available")
        return rate
