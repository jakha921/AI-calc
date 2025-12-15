from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class CurrencyEnum(str, Enum):
    USD = "USD"
    EUR = "EUR"
    RUB = "RUB"
    CNY = "CNY"
    UZS = "UZS"


class CalculationRequest(BaseModel):
    """Запрос на расчет таможенных платежей"""

    code: str = Field(..., min_length=4, max_length=10, description="Код ТН ВЭД (4-10 цифр)")
    price: float = Field(..., gt=0, description="Стоимость товара (инвойс)")
    currency: CurrencyEnum = Field(default=CurrencyEnum.USD, description="Валюта инвойса")

    # Для специфических ставок
    weight: Optional[float] = Field(None, ge=0, description="Вес товара в кг")
    quantity: Optional[int] = Field(None, ge=0, description="Количество единиц товара")

    # Дополнительные расходы
    delivery_cost: Optional[float] = Field(0.0, ge=0, description="Стоимость доставки")
    insurance_cost: Optional[float] = Field(0.0, ge=0, description="Стоимость страховки")

    # Страна происхождения
    country_origin: Optional[str] = Field(None, min_length=2, max_length=2, description="Код страны происхождения (ISO 3166-1 alpha-2)")
    has_origin_certificate: bool = Field(False, description="Наличие сертификата происхождения СТ-1")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "8703231981",
                "price": 10000,
                "currency": "USD",
                "weight": 500,
                "country_origin": "CN",
                "delivery_cost": 500,
                "insurance_cost": 100,
                "has_origin_certificate": False,
            }
        }


class PaymentDetail(BaseModel):
    """Детализация одного вида платежа"""

    name: str = Field(..., description="Наименование платежа")
    name_ru: str = Field(..., description="Наименование платежа (рус)")
    base_amount: float = Field(..., description="База начисления (UZS)")
    rate: str = Field(..., description="Ставка (% или специфическая)")
    amount_uzs: float = Field(..., description="Сумма в UZS")
    amount_usd: float = Field(..., description="Сумма в USD")


class CalculationResponse(BaseModel):
    """Ответ с результатами расчета"""

    # Исходные данные
    tn_ved_code: str
    tn_ved_description: str
    invoice_amount_uzs: float
    customs_value_uzs: float  # Таможенная стоимость

    # Применяемые ставки
    duty_rate: str
    excise_rate: str
    vat_rate: str

    # Детализация платежей
    payments: List[PaymentDetail]

    # Итоги
    total_uzs: float = Field(..., description="Итого к уплате в UZS")
    total_usd: float = Field(..., description="Итого к уплате в USD")

    # Курс валюты на дату расчета
    exchange_rate: float
    exchange_rate_date: str

    # Дополнительная информация
    country_origin: Optional[str] = None
    trade_regime: str = Field(..., description="Торговый режим")
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "tn_ved_code": "8703231981",
                "tn_ved_description": "Автомобили легковые...",
                "invoice_amount_uzs": 125000000,
                "customs_value_uzs": 132500000,
                "duty_rate": "30%",
                "excise_rate": "0%",
                "vat_rate": "12%",
                "payments": [
                    {
                        "name": "Customs clearance fee",
                        "name_ru": "Сбор за таможенное оформление",
                        "base_amount": 132500000,
                        "rate": "0.2%",
                        "amount_uzs": 265000,
                        "amount_usd": 21.2,
                    }
                ],
                "total_uzs": 55750000,
                "total_usd": 4460,
                "exchange_rate": 12500,
                "exchange_rate_date": "2024-01-15",
                "trade_regime": "MFN (1x)",
            }
        }
