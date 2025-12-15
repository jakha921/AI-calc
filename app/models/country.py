from sqlalchemy import Column, Integer, String, Boolean, Text
from app.db.database import Base


class Country(Base):
    """Страны и их торговые режимы"""

    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(2), unique=True, nullable=False, index=True)  # ISO 3166-1 alpha-2
    code_alpha3 = Column(String(3), nullable=True)  # ISO 3166-1 alpha-3
    name = Column(String(100), nullable=False)
    name_ru = Column(String(100), nullable=True)

    # Trade regime flags
    is_free_trade = Column(Boolean, default=False)  # Режим свободной торговли (пошлина 0%)
    is_mfn = Column(Boolean, default=True)  # Режим наибольшего благоприятствования (1x пошлина)
    is_cis = Column(Boolean, default=False)  # СНГ

    # Special economic zones
    is_sez = Column(Boolean, default=False)  # Особая экономическая зона

    # Notes
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Country {self.code}: {self.name}>"

    @property
    def duty_multiplier(self) -> float:
        """
        Returns duty multiplier based on trade regime:
        - Free trade: 0.0 (no duty)
        - MFN (most favored nation): 1.0 (standard duty)
        - Unknown/Other: 2.0 (double duty)
        """
        if self.is_free_trade:
            return 0.0
        elif self.is_mfn:
            return 1.0
        else:
            return 2.0
