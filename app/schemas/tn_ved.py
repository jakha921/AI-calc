from pydantic import BaseModel, Field
from typing import Optional, List


class TNVedCodeSchema(BaseModel):
    """Схема для кода ТН ВЭД"""

    id: int
    code: str
    description: str
    description_ru: Optional[str] = None
    parent_code: Optional[str] = None
    level: int

    class Config:
        from_attributes = True


class TNVedCodeSearchResult(BaseModel):
    """Результат поиска кодов ТН ВЭД"""

    code: str = Field(..., description="Код ТН ВЭД")
    description: str = Field(..., description="Описание товара")
    level: int = Field(..., description="Уровень иерархии")

    class Config:
        from_attributes = True


class TNVedSearchResponse(BaseModel):
    """Ответ на поиск"""

    query: str
    results: List[TNVedCodeSearchResult]
    total: int
