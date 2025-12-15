#!/usr/bin/env python3
"""
Скрипт инициализации базы данных с тестовыми данными
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal, init_db
from app.models.tn_ved import TNVedCode
from app.models.tariff import TariffRate, ExciseRate
from app.models.country import Country
from app.services.currency_service import CurrencyService


# Sample TN VED codes with rates
SAMPLE_TN_VED_CODES = [
    {
        "code": "8703231981",
        "description": "Motor vehicles for transport of persons, engine capacity 1500-3000 cc",
        "description_ru": "Автомобили легковые с двигателем от 1500 до 3000 куб.см",
        "level": 10,
        "duty_rate": 30.0,
        "excise_rate": 0.0,
    },
    {
        "code": "8703231010",
        "description": "New motor vehicles, engine 1500-2500 cc",
        "description_ru": "Новые автомобили легковые с двигателем 1500-2500 куб.см",
        "level": 10,
        "duty_rate": 30.0,
        "excise_rate": 0.0,
    },
    {
        "code": "8471300000",
        "description": "Portable automatic data processing machines (laptops)",
        "description_ru": "Портативные компьютеры (ноутбуки)",
        "level": 10,
        "duty_rate": 0.0,
        "excise_rate": 0.0,
    },
    {
        "code": "8517120000",
        "description": "Mobile phones",
        "description_ru": "Мобильные телефоны",
        "level": 10,
        "duty_rate": 0.0,
        "excise_rate": 0.0,
    },
    {
        "code": "6204430000",
        "description": "Women's dresses of synthetic fibres",
        "description_ru": "Платья женские из синтетических волокон",
        "level": 10,
        "duty_rate": 20.0,
        "excise_rate": 0.0,
    },
    {
        "code": "6403990000",
        "description": "Footwear with leather uppers",
        "description_ru": "Обувь с верхом из натуральной кожи",
        "level": 10,
        "duty_rate": 15.0,
        "excise_rate": 0.0,
    },
    {
        "code": "8528720000",
        "description": "Television receivers, colour",
        "description_ru": "Телевизоры цветные",
        "level": 10,
        "duty_rate": 15.0,
        "excise_rate": 0.0,
    },
    {
        "code": "8418100000",
        "description": "Combined refrigerator-freezers",
        "description_ru": "Холодильники-морозильники комбинированные",
        "level": 10,
        "duty_rate": 15.0,
        "excise_rate": 0.0,
    },
    {
        "code": "8450110000",
        "description": "Fully-automatic washing machines",
        "description_ru": "Стиральные машины автоматические",
        "level": 10,
        "duty_rate": 15.0,
        "excise_rate": 0.0,
    },
    {
        "code": "2203000000",
        "description": "Beer made from malt",
        "description_ru": "Пиво солодовое",
        "level": 10,
        "duty_rate": 30.0,
        "excise_rate": 25.0,
    },
    {
        "code": "2204100000",
        "description": "Sparkling wine",
        "description_ru": "Вина игристые",
        "level": 10,
        "duty_rate": 70.0,
        "excise_rate": 40.0,
    },
    {
        "code": "2402200000",
        "description": "Cigarettes containing tobacco",
        "description_ru": "Сигареты с табаком",
        "level": 10,
        "duty_rate": 30.0,
        "excise_rate": 35.0,
    },
    {
        "code": "8703000000",
        "description": "Motor cars and vehicles for transport of persons",
        "description_ru": "Автомобили легковые и транспортные средства для перевозки людей",
        "level": 4,
        "duty_rate": 30.0,
        "excise_rate": 0.0,
    },
    {
        "code": "8471000000",
        "description": "Automatic data processing machines (computers)",
        "description_ru": "Вычислительные машины автоматические (компьютеры)",
        "level": 4,
        "duty_rate": 0.0,
        "excise_rate": 0.0,
    },
    {
        "code": "8517000000",
        "description": "Telephone sets and communication apparatus",
        "description_ru": "Телефонные аппараты и аппаратура связи",
        "level": 4,
        "duty_rate": 0.0,
        "excise_rate": 0.0,
    },
]

# Countries with trade regimes
COUNTRIES = [
    {"code": "RU", "code_alpha3": "RUS", "name": "Russia", "name_ru": "Россия", "is_free_trade": True, "is_mfn": True, "is_cis": True},
    {"code": "KZ", "code_alpha3": "KAZ", "name": "Kazakhstan", "name_ru": "Казахстан", "is_free_trade": True, "is_mfn": True, "is_cis": True},
    {"code": "BY", "code_alpha3": "BLR", "name": "Belarus", "name_ru": "Беларусь", "is_free_trade": True, "is_mfn": True, "is_cis": True},
    {"code": "KG", "code_alpha3": "KGZ", "name": "Kyrgyzstan", "name_ru": "Кыргызстан", "is_free_trade": True, "is_mfn": True, "is_cis": True},
    {"code": "TJ", "code_alpha3": "TJK", "name": "Tajikistan", "name_ru": "Таджикистан", "is_free_trade": True, "is_mfn": True, "is_cis": True},
    {"code": "AM", "code_alpha3": "ARM", "name": "Armenia", "name_ru": "Армения", "is_free_trade": True, "is_mfn": True, "is_cis": True},
    {"code": "AZ", "code_alpha3": "AZE", "name": "Azerbaijan", "name_ru": "Азербайджан", "is_free_trade": True, "is_mfn": True, "is_cis": True},
    {"code": "MD", "code_alpha3": "MDA", "name": "Moldova", "name_ru": "Молдова", "is_free_trade": True, "is_mfn": True, "is_cis": True},
    {"code": "UA", "code_alpha3": "UKR", "name": "Ukraine", "name_ru": "Украина", "is_free_trade": True, "is_mfn": True, "is_cis": True},
    {"code": "GE", "code_alpha3": "GEO", "name": "Georgia", "name_ru": "Грузия", "is_free_trade": True, "is_mfn": True, "is_cis": False},
    {"code": "CN", "code_alpha3": "CHN", "name": "China", "name_ru": "Китай", "is_free_trade": False, "is_mfn": True, "is_cis": False},
    {"code": "KR", "code_alpha3": "KOR", "name": "South Korea", "name_ru": "Южная Корея", "is_free_trade": False, "is_mfn": True, "is_cis": False},
    {"code": "JP", "code_alpha3": "JPN", "name": "Japan", "name_ru": "Япония", "is_free_trade": False, "is_mfn": True, "is_cis": False},
    {"code": "DE", "code_alpha3": "DEU", "name": "Germany", "name_ru": "Германия", "is_free_trade": False, "is_mfn": True, "is_cis": False},
    {"code": "US", "code_alpha3": "USA", "name": "United States", "name_ru": "США", "is_free_trade": False, "is_mfn": True, "is_cis": False},
    {"code": "TR", "code_alpha3": "TUR", "name": "Turkey", "name_ru": "Турция", "is_free_trade": False, "is_mfn": True, "is_cis": False},
    {"code": "IN", "code_alpha3": "IND", "name": "India", "name_ru": "Индия", "is_free_trade": False, "is_mfn": True, "is_cis": False},
    {"code": "GB", "code_alpha3": "GBR", "name": "United Kingdom", "name_ru": "Великобритания", "is_free_trade": False, "is_mfn": True, "is_cis": False},
]


async def init_sample_data():
    """Initialize database with sample data"""
    print("Initializing database...")

    # Create tables
    await init_db()
    print("Tables created")

    async with AsyncSessionLocal() as session:
        # Add TN VED codes with rates
        print("Adding TN VED codes...")
        for code_data in SAMPLE_TN_VED_CODES:
            # Check if exists
            from sqlalchemy import select
            result = await session.execute(
                select(TNVedCode).where(TNVedCode.code == code_data["code"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                tn_ved = TNVedCode(
                    code=code_data["code"],
                    description=code_data["description"],
                    description_ru=code_data["description_ru"],
                    level=code_data["level"],
                )
                session.add(tn_ved)
                await session.flush()

                # Add tariff rate
                tariff = TariffRate(
                    code_id=tn_ved.id,
                    import_duty_rate=code_data["duty_rate"],
                    vat_rate=12.0,
                )
                session.add(tariff)

                # Add excise rate if applicable
                if code_data["excise_rate"] > 0:
                    excise = ExciseRate(
                        code_id=tn_ved.id,
                        excise_rate=code_data["excise_rate"],
                    )
                    session.add(excise)

        print(f"Added {len(SAMPLE_TN_VED_CODES)} TN VED codes")

        # Add countries
        print("Adding countries...")
        for country_data in COUNTRIES:
            result = await session.execute(
                select(Country).where(Country.code == country_data["code"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                country = Country(**country_data)
                session.add(country)

        print(f"Added {len(COUNTRIES)} countries")

        await session.commit()

        # Update currency rates
        print("Updating currency rates...")
        try:
            currency_service = CurrencyService(session)
            count = await currency_service.update_rates()
            print(f"Updated {count} currency rates")
        except Exception as e:
            print(f"Warning: Could not update currency rates: {e}")

    print("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_sample_data())
