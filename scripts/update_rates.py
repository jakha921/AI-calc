#!/usr/bin/env python3
"""
Скрипт обновления курсов валют от ЦБ Узбекистана
"""
import asyncio
import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal, init_db
from app.services.currency_service import CurrencyService


async def update_currency_rates():
    """Update currency rates from CBU"""
    print(f"Updating currency rates for {date.today()}...")

    # Initialize database
    await init_db()

    async with AsyncSessionLocal() as session:
        service = CurrencyService(session)

        try:
            count = await service.update_rates()
            print(f"Successfully updated {count} currency rates")

            # Show main rates
            rates_response = await service.get_all_rates()
            print("\nCurrent rates:")
            for rate in rates_response.rates:
                if rate.code in ['USD', 'EUR', 'RUB', 'CNY']:
                    print(f"  {rate.code}: {rate.rate:,.2f} UZS")

        except Exception as e:
            print(f"Error updating rates: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(update_currency_rates())
