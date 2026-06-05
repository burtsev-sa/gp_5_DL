import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
import time
from pathlib import Path

brands = ['bmw', 'mercedes-benz', 'audi', 'toyota', 'chevrolet', 'kia', 'hyundai', 'lexus']

from logs.logger import logger
log = logger()

# https://brightdata.com/blog/web-data/web-scraping-without-getting-blocked
# headers + набор разных user_agents, которые каждый раз выбираются рандомно. из статьи убран мобильный user_agent из-за другой мобильной страницы m.kolesa.kz
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.google.com/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Upgrade-Insecure-Requests": "1",
}

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
]

headers['User-Agent'] = random.choice(user_agents)

brand = input('Выберите марку. Доступные: bmw, mercedes-benz, audi, toyota, chevrolet, kia, hyundai, lexus: ')

if brand not in brands:
    print('Неверно введен бренд')
    exit()

try:
    pages = input('Диапазон странц через пробел (например: 1 5 - т.е. с 1 по 5 страницу включительно): ').split(' ')
    page0 = int(pages[0])
    page1 = int(pages[1])
except:
    print('Неверно введены страницы')
    exit()

log.info(f'Выбранная марка: {brand} | страницы: с {page0} по {page1}')

output_filename = f'{brand}_{page0}_{page1}'

total_start = time.perf_counter() # старт замера времени для всех страниц

rows = []

for page in range(page0, page1 + 1):
    try:
        page_start = time.perf_counter()
        if page == 1:
            url = f'https://kolesa.kz/cars/{brand}/avtomobili-s-probegom/?price%5Bfrom%5D=2000000&price%5Bto%5D=60000000'
        else:
            url += f'&page={page}'

        log.info(f'Получаем список объявлений для {brand.upper()}, страница: {page}')

        try:
            response = requests.get(url, timeout=15, headers=headers)
            log.info(f'Открыта страница {page} | {brand.upper()}')
        except:
            log.error(f'Ошибка открытия страницы {url}')

        soup = BeautifulSoup(response.text, 'html.parser')

        cards = soup.find_all(class_='a-card')
        log.info(f'Получены карточек для страницы {page} | {brand.upper()}')
    except:
        log.error(f'Неизвестная ошибка получения страницы {page} | {brand.upper()}')
        continue

    for card in cards:
        start = time.perf_counter() # старт замера времени для объявления
        time.sleep(random.uniform(4, 8))
        try:
            detail_url = card.find(class_='a-card__link').get('href')
            detail_url = f'https://kolesa.kz{detail_url}'
        except:
            log.error(f'Ошибка получения ссылки card = {card} | страница {page} | {brand.upper()}')
            continue
        try:
            try:
                headers['User-Agent'] = random.choice(user_agents)
                detail_response = requests.get(detail_url, timeout=15, headers=headers)
                log.info(f'Открыто объявление {detail_url}')
            except:
                log.error(f'Ошибка открытия объявления {detail_url}')

            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')

            card_id = detail_url.replace('https://kolesa.kz/a/show/', '').split('?')[0]

            title = detail_soup.find('h1')
            # https://stackoverflow.com/questions/48778818/get-itemprop-with-beautifulsoup
            car_brand = title.find('span', itemprop='brand').text.strip()
            car_model = title.find('span', itemprop='name').text.strip()
            car_year = title.find(class_='year').text.strip()

            price = detail_soup.find(class_='offer__price').text.replace('₸', '').replace('\xa0', '').strip()

            params = detail_soup.find(class_='offer__parameters')

            body_type = detail_soup.find('dt', title='Кузов').find_next('dd').text
            try:
                #если электричка
                engine = detail_soup.find('dt', title='Двигатель').find_next('dd').text
                engine_volume = 0
                fuel_type = engine
            except:
                #если бенз/дизель/газ
                engine = detail_soup.find('dt', title='Объем двигателя, л').find_next('dd').text.strip()
                engine_volume = float(engine.split(' ')[0])
                fuel_type = engine.split(' ')[1][1:-1]
            try:
                mileage = int(detail_soup.find('dt', title='Пробег').find_next('dd').text.replace('км', '').replace(' ', '').strip())
            except:
                log.error(f'Отсутствует пробег для объявления {detail_url} | пропускаем')
                continue
            transmission = detail_soup.find('dt', title='Коробка передач').find_next('dd').text
            drive_type = detail_soup.find('dt', title='Привод').find_next('dd').text
            steering_wheel = detail_soup.find('dt', title='Руль').find_next('dd').text
            kz_registration = detail_soup.find('dt', title='Растаможен в Казахстане').find_next('dd').text

            row = {
                'id': card_id,
                'brand': car_brand,
                'model': car_model,
                'year': car_year,
                'body_type': body_type,
                'fuel_type': fuel_type,
                'engine_volume': engine_volume,
                'mileage': mileage,
                'transmission': transmission,
                'drive_type': drive_type,
                'steering_wheel': steering_wheel,
                'kz_registration': kz_registration,
                'price': price
            }

            rows.append(row)
            finish = time.perf_counter()
            res = finish - start
            log.info(f'Получено объявление {car_brand} {car_model} {price}₸. id = {card_id} | затрачено {res} сек.')
        except:
            log.error(f'Неизвестная ошибка получения объявления {detail_url}')

    page_finish = time.perf_counter()
    page_res = page_finish - page_start
    log.info(f'Страница {page} (для {brand.upper()}) собрана | затрачено {page_res} сек.')

    time.sleep(random.uniform(4, 8))

total_finish = time.perf_counter()
total_res = total_finish - total_start

df = pd.DataFrame(rows).to_csv(Path(f'data/raw/{output_filename}.csv'), index=False)

log.info(f'Датасет {output_filename}.csv для {brand.upper()}, страницы {page0} - {page1} собран | затрачено {total_res} сек.')
