from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base


class TNVedCode(Base):
    """ТН ВЭД коды товаров (товарная номенклатура внешнеэкономической деятельности)"""

    __tablename__ = "tn_ved_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    description_ru = Column(Text, nullable=True)  # Russian description
    parent_code = Column(String(10), ForeignKey("tn_ved_codes.code"), nullable=True)

    # Hierarchical level: 2-group, 4-position, 6-subposition, 8/10-item
    level = Column(Integer, nullable=False, default=10)

    # Relationships
    parent = relationship("TNVedCode", remote_side=[code], backref="children")
    tariff_rates = relationship("TariffRate", back_populates="tn_ved_code")
    excise_rates = relationship("ExciseRate", back_populates="tn_ved_code")

    # Indexes for search
    __table_args__ = (
        Index("idx_tn_ved_code_description", "description"),
        Index("idx_tn_ved_code_level", "level"),
    )

    def __repr__(self):
        return f"<TNVedCode {self.code}: {self.description[:50]}>"

    @property
    def group_code(self) -> str:
        """Returns 2-digit group code"""
        return self.code[:2] if self.code else ""

    @property
    def position_code(self) -> str:
        """Returns 4-digit position code"""
        return self.code[:4] if self.code else ""

    @property
    def subposition_code(self) -> str:
        """Returns 6-digit subposition code"""
        return self.code[:6] if self.code else ""
