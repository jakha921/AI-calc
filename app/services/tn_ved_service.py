"""
Сервис для работы с кодами ТН ВЭД
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
import logging

from app.models.tn_ved import TNVedCode
from app.models.tariff import TariffRate, ExciseRate
from app.schemas.tn_ved import TNVedCodeSchema, TNVedCodeSearchResult, TNVedSearchResponse

logger = logging.getLogger(__name__)


class TNVedService:
    """Сервис для поиска и работы с кодами ТН ВЭД"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        query: str,
        limit: int = 20,
        code_only: bool = False
    ) -> TNVedSearchResponse:
        """
        Search TN VED codes by code or description

        Args:
            query: Search query (code or text)
            limit: Maximum number of results
            code_only: Search only by code, not description

        Returns:
            TNVedSearchResponse with matching codes
        """
        query = query.strip()

        if code_only or query.isdigit():
            # Search by code prefix
            stmt = (
                select(TNVedCode)
                .where(TNVedCode.code.startswith(query))
                .order_by(TNVedCode.code)
                .limit(limit)
            )
        else:
            # Search by code or description
            search_term = f"%{query}%"
            stmt = (
                select(TNVedCode)
                .where(
                    or_(
                        TNVedCode.code.startswith(query),
                        TNVedCode.description.ilike(search_term),
                        TNVedCode.description_ru.ilike(search_term)
                    )
                )
                .order_by(TNVedCode.code)
                .limit(limit)
            )

        result = await self.db.execute(stmt)
        codes = result.scalars().all()

        return TNVedSearchResponse(
            query=query,
            results=[
                TNVedCodeSearchResult(
                    code=c.code,
                    description=c.description_ru or c.description,
                    level=c.level
                )
                for c in codes
            ],
            total=len(codes)
        )

    async def get_by_code(self, code: str) -> Optional[TNVedCode]:
        """
        Get TN VED code by exact code

        Args:
            code: 4-10 digit TN VED code

        Returns:
            TNVedCode or None
        """
        # Pad code to 10 digits if needed
        if len(code) < 10:
            code = code.ljust(10, "0")

        result = await self.db.execute(
            select(TNVedCode).where(TNVedCode.code == code)
        )
        return result.scalar_one_or_none()

    async def get_tariff_rate(self, code: str) -> Optional[TariffRate]:
        """
        Get tariff rate for a TN VED code

        Args:
            code: TN VED code

        Returns:
            TariffRate or None
        """
        tn_ved = await self.get_by_code(code)
        if not tn_ved:
            return None

        result = await self.db.execute(
            select(TariffRate).where(TariffRate.code_id == tn_ved.id)
        )
        return result.scalar_one_or_none()

    async def get_excise_rate(self, code: str) -> Optional[ExciseRate]:
        """
        Get excise rate for a TN VED code

        Args:
            code: TN VED code

        Returns:
            ExciseRate or None
        """
        tn_ved = await self.get_by_code(code)
        if not tn_ved:
            return None

        result = await self.db.execute(
            select(ExciseRate).where(ExciseRate.code_id == tn_ved.id)
        )
        return result.scalar_one_or_none()

    async def get_with_rates(self, code: str) -> dict:
        """
        Get TN VED code with all associated rates

        Args:
            code: TN VED code

        Returns:
            Dictionary with code info and rates
        """
        tn_ved = await self.get_by_code(code)
        if not tn_ved:
            return None

        tariff = await self.get_tariff_rate(code)
        excise = await self.get_excise_rate(code)

        return {
            "code": tn_ved.code,
            "description": tn_ved.description_ru or tn_ved.description,
            "level": tn_ved.level,
            "tariff": {
                "import_duty_rate": tariff.import_duty_rate if tariff else 0,
                "per_unit_rate": tariff.per_unit_rate if tariff else 0,
                "measure_unit": tariff.measure_unit if tariff else None,
                "vat_rate": tariff.vat_rate if tariff else 12.0,
            } if tariff else None,
            "excise": {
                "excise_rate": excise.excise_rate if excise else 0,
                "excise_per_unit": excise.excise_per_unit if excise else 0,
                "excise_unit": excise.excise_unit if excise else None,
            } if excise else None,
        }

    async def create_code(self, code_data: dict) -> TNVedCode:
        """Create a new TN VED code"""
        tn_ved = TNVedCode(**code_data)
        self.db.add(tn_ved)
        await self.db.commit()
        await self.db.refresh(tn_ved)
        return tn_ved

    async def bulk_create_codes(self, codes_data: List[dict]) -> int:
        """
        Bulk create TN VED codes

        Args:
            codes_data: List of code dictionaries

        Returns:
            Number of codes created
        """
        count = 0
        for code_data in codes_data:
            # Check if exists
            existing = await self.get_by_code(code_data["code"])
            if not existing:
                tn_ved = TNVedCode(**code_data)
                self.db.add(tn_ved)
                count += 1

        await self.db.commit()
        logger.info(f"Created {count} TN VED codes")
        return count
