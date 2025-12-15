# Таможенный калькулятор

Веб-приложение для расчета таможенных платежей при импорте товаров в Узбекистан.

## Возможности

- Поиск товаров по коду ТН ВЭД или названию
- Расчет импортных пошлин, акцизов и НДС
- Учет страны происхождения и торгового режима
- Автоматическое обновление курсов валют от ЦБ Узбекистана
- Поддержка сертификата происхождения СТ-1

## Технологии

- **Backend**: Python 3.11, FastAPI
- **База данных**: PostgreSQL
- **Frontend**: HTML/CSS/JavaScript (без фреймворков)
- **Парсинг**: BeautifulSoup, python-docx, pandas

## Быстрый старт

### Вариант 1: Docker (рекомендуется)

```bash
# Клонировать репозиторий
git clone <repository-url>
cd customs-calculator

# Запустить с Docker Compose
docker-compose up -d

# Приложение доступно по адресу http://localhost:8000
```

### Вариант 2: Локальная установка

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt

# Создать файл .env
cp .env.example .env
# Отредактировать .env с вашими настройками БД

# Инициализировать базу данных
python scripts/init_db.py

# Запустить сервер
uvicorn app.main:app --reload
```

## API Endpoints

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/search?q=...` | Поиск товаров по коду или названию |
| GET | `/api/rates` | Получение текущих курсов валют |
| POST | `/api/calculate` | Расчет таможенных платежей |
| GET | `/api/code/{code}` | Информация о коде ТН ВЭД |
| POST | `/api/rates/update` | Обновление курсов валют |

### Пример запроса расчета

```bash
curl -X POST http://localhost:8000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "code": "8703231981",
    "price": 10000,
    "currency": "USD",
    "weight": 500,
    "country_origin": "CN",
    "delivery_cost": 500,
    "insurance_cost": 100,
    "has_origin_certificate": false
  }'
```

### Пример ответа

```json
{
  "tn_ved_code": "8703231981",
  "tn_ved_description": "Автомобили легковые с двигателем от 1500 до 3000 куб.см",
  "customs_value_uzs": 132500000,
  "duty_rate": "30%",
  "excise_rate": "0%",
  "vat_rate": "12%",
  "payments": [
    {
      "name_ru": "Сбор за таможенное оформление",
      "base_amount": 132500000,
      "rate": "0.2%",
      "amount_uzs": 265000,
      "amount_usd": 21.2
    },
    ...
  ],
  "total_uzs": 55750000,
  "total_usd": 4460,
  "trade_regime": "MFN (1x)"
}
```

## Структура проекта

```
customs-calculator/
├── app/
│   ├── api/            # API маршруты
│   ├── core/           # Конфигурация
│   ├── db/             # Подключение к БД
│   ├── models/         # SQLAlchemy модели
│   ├── parsers/        # Парсеры данных
│   ├── schemas/        # Pydantic схемы
│   ├── services/       # Бизнес-логика
│   └── main.py         # Точка входа
├── frontend/           # Статические файлы
├── scripts/            # Скрипты обслуживания
├── data/               # Файлы данных
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Обновление данных

### Обновление курсов валют

```bash
python scripts/update_rates.py
```

### Парсинг данных с lex.uz

```bash
python scripts/parse_lex.py
```

## Формула расчета

1. **Таможенная стоимость (ТС)** = Цена товара + Доставка + Страховка
2. **Сбор за таможенное оформление** = 0.2% от ТС (мин. 50 000, макс. 3 000 000 сум)
3. **Импортная пошлина** = ТС × Ставка пошлины × Множитель режима
4. **Акциз** = (ТС + Пошлина) × Ставка акциза
5. **НДС (QQS)** = (ТС + Пошлина + Акциз) × 12%
6. **Итого** = Сбор + Пошлина + Акциз + НДС

### Торговые режимы

| Режим | Множитель пошлины |
|-------|-------------------|
| Свободная торговля (СНГ + СТ-1) | 0% |
| Режим наибольшего благоприятствования | 1× |
| Неизвестная страна | 2× |

## Источники данных

- [Ставки пошлин](https://lex.uz/docs/3802366)
- [Ставки акцизов](https://lex.uz/docs/6718877)
- [Страны свободной торговли](https://lex.uz/docs/4911947)
- [Курсы валют ЦБ](https://cbu.uz)

## Настройка формул

Основные параметры расчета находятся в:
- `app/core/config.py` - базовые настройки (БРВ, ставка НДС)
- `app/services/calculation_service.py` - логика расчета

## Лицензия

MIT
