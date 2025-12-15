#!/usr/bin/env python3
"""
Скрипт парсинга данных с lex.uz
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parsers.lex_parser import LexUzParser


async def main():
    """Parse data from lex.uz"""
    print("Parsing lex.uz for customs data...")

    async with LexUzParser() as parser:
        # Parse duty rates
        print("\n1. Parsing duty rates...")
        try:
            duty_rates = await parser.parse_duty_rates()
            print(f"   Found {len(duty_rates)} duty rates")
            for rate in duty_rates[:5]:
                print(f"   - {rate['code']}: {rate['rate']}%")
        except Exception as e:
            print(f"   Error parsing duty rates: {e}")

        # Parse excise rates
        print("\n2. Parsing excise rates...")
        try:
            excise_rates = await parser.parse_excise_rates()
            print(f"   Found {len(excise_rates)} excise rates")
            for rate in excise_rates[:5]:
                print(f"   - {rate['code']}: {rate['rate']}%")
        except Exception as e:
            print(f"   Error parsing excise rates: {e}")

        # Parse free trade countries
        print("\n3. Parsing free trade countries...")
        try:
            countries = await parser.parse_free_trade_countries()
            print(f"   Found {len(countries)} countries")
            for country in countries[:5]:
                print(f"   - {country['name_ru']}")
        except Exception as e:
            print(f"   Error parsing countries: {e}")

    print("\nParsing complete!")
    print("\nNote: The parsed data structure may need adjustment based on")
    print("the actual HTML structure of lex.uz documents.")


if __name__ == "__main__":
    asyncio.run(main())
