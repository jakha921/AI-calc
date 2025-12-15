from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base


class TariffRate(Base):
    """Ставки импортных пошлин"""

    __tablename__ = "tariff_rates"

    id = Column(Integer, primary_key=True, index=True)
    code_id = Column(Integer, ForeignKey("tn_ved_codes.id"), nullable=False)

    # Import duty rate (адвалорная ставка в %)
    import_duty_rate = Column(Float, nullable=True, default=0.0)

    # Specific rate (специфическая ставка, например $ за кг)
    per_unit_rate = Column(Float, nullable=True, default=0.0)
    measure_unit = Column(String(20), nullable=True)  # кг, шт, литр, etc.

    # Combined duty (комбинированная ставка)
    is_combined = Column(Boolean, default=False)
    min_rate = Column(Float, nullable=True)  # минимальная ставка для комбинированной

    # VAT rate (НДС) - обычно 12%
    vat_rate = Column(Float, default=12.0)

    # Notes
    notes = Column(Text, nullable=True)

    # Source document reference
    source_doc = Column(String(255), nullable=True)

    # Relationship
    tn_ved_code = relationship("TNVedCode", back_populates="tariff_rates")

    def __repr__(self):
        return f"<TariffRate code_id={self.code_id} duty={self.import_duty_rate}%>"


class ExciseRate(Base):
    """Ставки акцизного налога"""

    __tablename__ = "excise_rates"

    id = Column(Integer, primary_key=True, index=True)
    code_id = Column(Integer, ForeignKey("tn_ved_codes.id"), nullable=False)

    # Excise rate (акциз)
    excise_rate = Column(Float, nullable=True, default=0.0)  # % от базы
    excise_per_unit = Column(Float, nullable=True, default=0.0)  # специфическая ставка
    excise_unit = Column(String(20), nullable=True)  # единица измерения

    # Additional excise info
    is_ad_valorem = Column(Boolean, default=True)  # адвалорная или специфическая

    # Notes
    notes = Column(Text, nullable=True)
    source_doc = Column(String(255), nullable=True)

    # Relationship
    tn_ved_code = relationship("TNVedCode", back_populates="excise_rates")

    def __repr__(self):
        return f"<ExciseRate code_id={self.code_id} rate={self.excise_rate}%>"
