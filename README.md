# Групповой проект 5: Deep Learning

### **Подготовка**

0. Склонировать репозиторий

```bash
git clone https://github.com/ylevennn/smadimo-gp-2
```

1. Создать и активировать окружение

- На MacOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

- На Windows (cmd):

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Установить требуемые библиотеки

```bash
pip install -r requirements.txt
```

### Подготовка датасетов для работы

0. Сбор данных производился через парсер `kolesa_parser.py`. Все нужные для дальнейших пунктов данные лежат в `data/raw`.

1. Объединить все спаршенные датасеты - запустить ноутбук `merge_parsed.ipynb`

2. Провести базовую очистку датасета - запустить ноутбук `prepare_raw_data.ipynb`

3. Разделить датасет на датасет под задачу на табличных данных (`df_table.csv`) и на изображениях (`df_images.csv`) - запустить ноутбук `split_datasets.ipynb`

Итого: `clean_df` => `merge_parsed.ipynb` -> `prepare_raw_data.ipynb` -> `split_datasets.ipynb` => `df_table.csv` & `df_images.ipynb`