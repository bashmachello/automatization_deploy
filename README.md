# Автоматизация обработки данных торговой сети

## Описание проекта

Проект автоматизирует обработку ежедневных выгрузок из кассового софта торговой сети. 
Данные генерируются (эмуляция работы касс), загружаются в MinIO (S3-совместимое хранилище),
далее поступают в PostgreSQL для анализа и визуализируются через Metabase.

### Технологии
- **Python 3.12+** - генерация и обработка данных
- **PostgreSQL 17** - хранение данных
- **MinIO** - объектное хранилище для CSV файлов
- **Metabase** - BI аналитика и дашборды
- **Docker** - контейнеризация инфраструктуры
- **Cron** - планировщик ежедневных задач

### Структура проекта
```
automatization_deploy/
├── etl/                          # ETL модули
│   ├── __init__.py
│   ├── run.py                    # Основной скрипт генерации
│   └── export_to_db.py           # Загрузка из MinIO в PostgreSQL
├── generator/                    # Генерация данных
│   ├── __init__.py
│   └── gen_sales.py
├── storage/                      # Работа с хранилищами
│   ├── __init__.py
│   ├── minio_client.py
│   └── pgdb.py
├── utils/                        # Утилиты
│   ├── __init__.py
│   ├── logger.py
│   └── tg_handler.py
├── logs/                         # Логи (создаётся автоматически)
├── docker-compose.yml
├── config.py                     # Данные для изменения
├── create_tables.sql             # SQL схема БД
├── drop_tables.sql               # Удаление БД
├── requirements.txt
├── .env.example                  # Шаблон переменных окружения
└── README.md
```

## Требования

- Ubuntu 22.04 / 24.04 (или любой Linux)
- Docker и Docker Compose
- Python 3.12+
- Git
- 4GB RAM (рекомендуется 8GB)
- Свободные порты: 5432, 9000, 9001, 3000

---

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/bashmachello/automatization_deploy.git
cd automatization_deploy
```

### 2. Установка системных зависимостей

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv docker.io docker-compose
```

### 3. Настройка виртуального окружения Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` на основе примера:

```bash
cp .env.example .env
nano .env
```

Заполните файл своими значениями:

```env
# PostgreSQL для данных
DB_HOST=localhost
DB_NAME=sales_db
DB_USER=postgres
DB_PASSWORD=your_strong_password

# MinIO
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=sales-data

# Metabase
METABASE_DB_PASSWORD=metabase_secure_password

# Telegram (опционально - можно оставить пустыми)
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
```

### 5. Запуск Docker контейнеров

```bash
docker-compose up -d
```

### 6. Создание таблиц в PostgreSQL

```bash
sudo docker exec -i sales_postgres psql -U postgres -d sales_db < create_tables.sql
```
### и удаление таблиц в PostgreSQL
```bash
sudo docker exec -i sales_postgres psql -U postgres -d sales_db < drop_tables.sql
```

### 7. Первый ручной запуск ETL процесса

#### Генерация данных и загрузка в MinIO:
```bash
python -m etl.run
```

#### Загрузка данных из MinIO в PostgreSQL:
```bash
python -m etl.export_to_db
```

### 8. Проверка работоспособности

#### Проверка данных в MinIO:
- Откройте браузер: `http://localhost:9001`
- Логин: `minioadmin`
- Пароль: из `.env` (`MINIO_SECRET_KEY`)
- Проверьте наличие файлов в bucket `sales-data`

#### Проверка данных в PostgreSQL:
```bash
sudo docker exec -it sales_postgres psql -U postgres -d sales_db -c "SELECT COUNT(*) FROM sales;"
```

#### Проверка Metabase:
- Откройте браузер: `http://localhost:3000`
- Настройте подключение к вашей БД `sales_db`

---

## Настройка автоматического запуска (Cron)


### Настройте расписание в crontab:

```bash
crontab -e
```

Добавьте строки:

```bash
# Генерация данных: каждый день в 23:00, кроме воскресенья
00 23 * * 1-6 cd $HOME/automatization_deploy && $HOME/automatization_deploy/venv/bin/python -m etl.run

# Загрузка в БД: каждый день в 23:30
30 23 * * * cd $HOME/automatization_deploy && $HOME/automatization_deploy/venv/bin/python -m etl.export_to_db
```

## Остановка проекта

### Остановка Docker контейнеров:
```bash
docker-compose down
```

### Полная остановка с удалением томов (очистка данных):
```bash
docker-compose down -v
```

### Деактивация виртуального окружения:
```bash
deactivate
```

## Авторы

Проект разработан в рамках учебного задания по автоматизации ETL процессов.

## Лицензия

MIT

