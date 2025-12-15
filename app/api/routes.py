"""
API маршруты для таможенного калькулятора
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.calculation_service import CalculationService
from app.services.currency_service import CurrencyService
from app.services.tn_ved_service import TNVedService
from app.schemas.calculation import CalculationRequest, CalculationResponse
from app.schemas.currency import CurrencyRatesResponse
from app.schemas.tn_ved import TNVedSearchResponse

router = APIRouter(prefix="/api", tags=["Customs Calculator"])


@router.get("/search", response_model=TNVedSearchResponse)
async def search_tn_ved(
    q: str = Query(..., min_length=2, description="Поисковый запрос (код или название)"),
    limit: int = Query(20, ge=1, le=100, description="Максимальное количество результатов"),
    db: AsyncSession = Depends(get_db),
):
    """
    Поиск товаров по коду ТН ВЭД или названию

    - Поддерживает поиск по частичному коду (например, "8703")
    - Поддерживает поиск по описанию товара
    - Возвращает список подходящих кодов с описаниями
    """
    service = TNVedService(db)
    return await service.search(q, limit=limit)


@router.get("/rates", response_model=CurrencyRatesResponse)
async def get_currency_rates(
    date_str: Optional[str] = Query(
        None,
        alias="date",
        description="Дата курсов в формате YYYY-MM-DD (по умолчанию: сегодня)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Получение текущих курсов валют от ЦБ Узбекистана

    Возвращает курсы основных валют (USD, EUR, RUB и др.) к узбекскому суму.
    """
    service = CurrencyService(db)

    rate_date = None
    if date_str:
        try:
            rate_date = date.fromisoformat(date_str)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Неверный формат даты. Используйте YYYY-MM-DD"
            )

    return await service.get_all_rates(rate_date)


@router.post("/calculate", response_model=CalculationResponse)
async def calculate_customs(
    request: CalculationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Расчет таможенных платежей при импорте

    Принимает данные о товаре и возвращает детальную разбивку платежей:
    - Сбор за таможенное оформление
    - Импортная пошлина
    - Акцизный налог
    - НДС (QQS)
    - Итоговая сумма

    Учитывает:
    - Страну происхождения и торговый режим
    - Наличие сертификата происхождения СТ-1
    - Текущие курсы валют
    """
    service = CalculationService(db)

    try:
        result = await service.calculate(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка расчета: {str(e)}"
        )


@router.get("/code/{code}")
async def get_code_info(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Получение информации о коде ТН ВЭД

    Возвращает описание товара и применимые ставки.
    """
    service = TNVedService(db)
    code_info = await service.get_with_rates(code)

    if not code_info:
        raise HTTPException(
            status_code=404,
            detail=f"Код ТН ВЭД {code} не найден"
        )

    return code_info


@router.post("/rates/update")
async def update_currency_rates(
    db: AsyncSession = Depends(get_db),
):
    """
    Обновление курсов валют из ЦБ Узбекистана

    Загружает актуальные курсы валют и сохраняет в базу данных.
    """
    service = CurrencyService(db)
    try:
        count = await service.update_rates()
        return {"message": f"Обновлено {count} курсов валют", "count": count}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обновления курсов: {str(e)}"
        )
