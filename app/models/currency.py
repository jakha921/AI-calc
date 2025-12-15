from sqlalchemy import Column, Integer, String, Float, DateTime, Date
from datetime import datetime
from app.db.database import Base


class Currency(Base):
    """Курсы валют от ЦБ Узбекистана"""

    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), nullable=False, index=True)  # USD, EUR, RUB, etc.
    ccy = Column(String(10), nullable=True)  # CBU currency code
    name = Column(String(100), nullable=False)
    name_ru = Column(String(100), nullable=True)

    # Rate to UZS
    rate = Column(Float, nullable=False)

    # Nominal (for some currencies like JPY it's 100)
    nominal = Column(Integer, default=1)

    # Date of the rate
    rate_date = Column(Date, nullable=False, index=True)

    # Update timestamp
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Currency {self.code}: {self.rate} UZS>"

    @property
    def rate_per_unit(self) -> float:
        """Returns rate per 1 unit of currency"""
        return self.rate / self.nominal if self.nominal else self.rate
