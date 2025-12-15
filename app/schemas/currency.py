from pydantic import BaseModel, Field
from typing import List
from datetime import date


class CurrencySchema(BaseModel):
    """Схема для курса валюты"""

    code: str = Field(..., description="Код валюты (USD, EUR, etc.)")
    name: str = Field(..., description="Название валюты")
    rate: float = Field(..., description="Курс к UZS")
    nominal: int = Field(default=1, description="Номинал")
    rate_date: date = Field(..., description="Дата курса")

    class Config:
        from_attributes = True

    @property
    def rate_per_unit(self) -> float:
        return self.rate / self.nominal if self.nominal else self.rate


class CurrencyRatesResponse(BaseModel):
    """Ответ с курсами валют"""

    rates: List[CurrencySchema]
    date: date
    source: str = "cbu.uz"
