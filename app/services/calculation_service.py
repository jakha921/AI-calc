"""
Сервис расчета таможенных платежей
"""
from datetime import date
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.country import Country
from app.services.currency_service import CurrencyService
from app.services.tn_ved_service import TNVedService
from app.schemas.calculation import (
    CalculationRequest,
    CalculationResponse,
    PaymentDetail,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class CalculationService:
    """
    Сервис для расчета таможенных платежей при импорте в Узбекистан

    Формула расчета:
    1. Таможенная стоимость (ТС) = Цена товара + Доставка + Страховка
    2. Сбор за таможенное оформление = Фиксированная сумма (БРВ) или % от ТС
    3. Импортная пошлина = ТС * Ставка пошлины (или специфическая ставка * количество)
    4. Акциз = (ТС + Импортная пошлина) * Ставка акциза
    5. НДС (QQS) = (ТС + Пошлина + Акциз) * 12%
    6. Итого = Сбор + Пошлина + Акциз + НДС
    """

    # Customs clearance fee rates
    CLEARANCE_FEE_RATE = 0.002  # 0.2% от таможенной стоимости
    CLEARANCE_FEE_MIN = 50000  # минимум 50 000 сум
    CLEARANCE_FEE_MAX = 3000000  # максимум 3 000 000 сум

    def __init__(self, db: AsyncSession):
        self.db = db
        self.currency_service = CurrencyService(db)
        self.tn_ved_service = TNVedService(db)

    async def calculate(self, request: CalculationRequest) -> CalculationResponse:
        """
        Calculate customs payments for import

        Args:
            request: Calculation request with product details

        Returns:
            CalculationResponse with detailed breakdown
        """
        # Get exchange rate
        usd_rate = await self.currency_service.get_usd_rate()
        rate_date = date.today()

        # Get rate for invoice currency
        if request.currency.value == "UZS":
            invoice_rate = 1.0
        else:
            invoice_rate = await self.currency_service.get_rate(request.currency.value)
            if invoice_rate is None:
                invoice_rate = usd_rate  # Fallback to USD

        # Calculate invoice amount in UZS
        invoice_amount_uzs = request.price * invoice_rate

        # Calculate customs value (таможенная стоимость)
        delivery_uzs = (request.delivery_cost or 0) * invoice_rate
        insurance_uzs = (request.insurance_cost or 0) * invoice_rate
        customs_value_uzs = invoice_amount_uzs + delivery_uzs + insurance_uzs

        # Get TN VED code info and rates
        code_info = await self.tn_ved_service.get_with_rates(request.code)

        # Default rates if not found in DB
        duty_rate = 0.0
        excise_rate = 0.0
        vat_rate = settings.VAT_RATE
        per_unit_rate = 0.0
        measure_unit = None

        if code_info and code_info.get("tariff"):
            duty_rate = code_info["tariff"].get("import_duty_rate", 0) or 0
            per_unit_rate = code_info["tariff"].get("per_unit_rate", 0) or 0
            measure_unit = code_info["tariff"].get("measure_unit")
            vat_rate = code_info["tariff"].get("vat_rate", 12.0) or 12.0

        if code_info and code_info.get("excise"):
            excise_rate = code_info["excise"].get("excise_rate", 0) or 0

        # Determine trade regime and duty multiplier
        duty_multiplier = 1.0
        trade_regime = "MFN (1x)"

        if request.country_origin:
            country = await self._get_country(request.country_origin)
            if country:
                if country.is_free_trade and request.has_origin_certificate:
                    duty_multiplier = 0.0
                    trade_regime = "Свободная торговля (0%)"
                elif country.is_mfn:
                    duty_multiplier = 1.0
                    trade_regime = "Режим наибольшего благоприятствования (1x)"
                else:
                    duty_multiplier = 2.0
                    trade_regime = "Неизвестная страна (2x)"
            else:
                duty_multiplier = 2.0
                trade_regime = "Неизвестная страна (2x)"

        # Calculate payments
        payments: List[PaymentDetail] = []

        # 1. Customs clearance fee (сбор за таможенное оформление)
        clearance_fee = self._calculate_clearance_fee(customs_value_uzs)
        payments.append(PaymentDetail(
            name="Customs clearance fee",
            name_ru="Сбор за таможенное оформление",
            base_amount=customs_value_uzs,
            rate=f"{self.CLEARANCE_FEE_RATE * 100}%",
            amount_uzs=clearance_fee,
            amount_usd=clearance_fee / usd_rate,
        ))

        # 2. Import duty (импортная пошлина)
        effective_duty_rate = duty_rate * duty_multiplier

        if per_unit_rate > 0 and request.weight:
            # Specific rate (специфическая ставка)
            import_duty = per_unit_rate * request.weight * usd_rate
            duty_rate_str = f"${per_unit_rate}/{measure_unit or 'кг'}"
        else:
            # Ad valorem rate (адвалорная ставка)
            import_duty = customs_value_uzs * (effective_duty_rate / 100)
            duty_rate_str = f"{effective_duty_rate}%"

        payments.append(PaymentDetail(
            name="Import duty",
            name_ru="Импортная пошлина",
            base_amount=customs_value_uzs,
            rate=duty_rate_str,
            amount_uzs=import_duty,
            amount_usd=import_duty / usd_rate,
        ))

        # 3. Excise tax (акцизный налог)
        excise_base = customs_value_uzs + import_duty
        excise_amount = excise_base * (excise_rate / 100)
        payments.append(PaymentDetail(
            name="Excise tax",
            name_ru="Акцизный налог",
            base_amount=excise_base,
            rate=f"{excise_rate}%",
            amount_uzs=excise_amount,
            amount_usd=excise_amount / usd_rate,
        ))

        # 4. VAT / НДС (QQS)
        vat_base = customs_value_uzs + import_duty + excise_amount
        vat_amount = vat_base * (vat_rate / 100)
        payments.append(PaymentDetail(
            name="VAT (QQS)",
            name_ru="НДС (QQS)",
            base_amount=vat_base,
            rate=f"{vat_rate}%",
            amount_uzs=vat_amount,
            amount_usd=vat_amount / usd_rate,
        ))

        # Calculate totals
        total_uzs = clearance_fee + import_duty + excise_amount + vat_amount
        total_usd = total_uzs / usd_rate

        # Build response
        return CalculationResponse(
            tn_ved_code=request.code,
            tn_ved_description=code_info["description"] if code_info else "Код не найден",
            invoice_amount_uzs=invoice_amount_uzs,
            customs_value_uzs=customs_value_uzs,
            duty_rate=duty_rate_str,
            excise_rate=f"{excise_rate}%",
            vat_rate=f"{vat_rate}%",
            payments=payments,
            total_uzs=total_uzs,
            total_usd=total_usd,
            exchange_rate=usd_rate,
            exchange_rate_date=rate_date.isoformat(),
            country_origin=request.country_origin,
            trade_regime=trade_regime,
            notes=self._generate_notes(request, code_info),
        )

    def _calculate_clearance_fee(self, customs_value: float) -> float:
        """Calculate customs clearance fee"""
        fee = customs_value * self.CLEARANCE_FEE_RATE
        fee = max(fee, self.CLEARANCE_FEE_MIN)
        fee = min(fee, self.CLEARANCE_FEE_MAX)
        return fee

    async def _get_country(self, country_code: str) -> Optional[Country]:
        """Get country by ISO code"""
        result = await self.db.execute(
            select(Country).where(Country.code == country_code.upper())
        )
        return result.scalar_one_or_none()

    def _generate_notes(self, request: CalculationRequest, code_info: dict) -> Optional[str]:
        """Generate notes for the calculation"""
        notes = []

        if not code_info:
            notes.append("Код ТН ВЭД не найден в базе, использованы нулевые ставки.")

        if request.has_origin_certificate and request.country_origin:
            notes.append("Применен сертификат происхождения СТ-1.")

        if not request.weight and code_info and code_info.get("tariff", {}).get("per_unit_rate"):
            notes.append("Для точного расчета укажите вес товара (применяется специфическая ставка).")

        return " ".join(notes) if notes else None
