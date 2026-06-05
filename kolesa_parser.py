import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from curl_cffi import requests as curl_requests

brands = ['bmw', 'mercedes-benz', 'audi', 'toyota', 'chevrolet', 'kia', 'hyundai', 'lexus']

from logs.logger import logger
log = logger()

# https://brightdata.com/blog/web-data/web-scraping-without-getting-blocked
# headers + набор разных user_agents, которые каждый раз выбираются рандомно. из статьи убран мобильный user_agent из-за другой мобильной страницы m.kolesa.kz
# + Manage TLS Fingerprinting. решение из статьи: use an HTTP client that impersonates a real browser’s TLS stack. будем использовать curl_requests вместо requests + параметр impersonate='chrome120' (везде зафиксируем эту версию)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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

# инициализируем сессию. это позволит больше быть похожим на поведение обычного браузера. через нее будем получать страницы
session = curl_requests.Session(impersonate='chrome120', timeout=15, headers=headers)

for page in range(page0, page1 + 1):
    try:
        page_start = time.perf_counter()
        if page == 1:
            url = f'https://kolesa.kz/cars/{brand}/avtomobili-s-probegom/?price%5Bfrom%5D=2000000&price%5Bto%5D=60000000'
        else:
            url = f'https://kolesa.kz/cars/{brand}/avtomobili-s-probegom/?price%5Bfrom%5D=2000000&price%5Bto%5D=60000000&page={page}'

        log.info(f'Получаем список объявлений для {brand.upper()}, страница: {page}')

        try:
            response = session.get(url)
            log.info(f'Открыта страница {page} | {brand.upper()}')
        except:
            log.error(f'Ошибка открытия страницы {url}')
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(detail_response.text)
            continue

        soup = BeautifulSoup(response.text, 'html.parser')

        cards = soup.find_all(class_='a-card')
        log.info(f'Получены карточек для страницы {page} | {brand.upper()}')
    except:
        log.error(f'Неизвестная ошибка получения страницы {page} | {brand.upper()}')
        with open(debug_filename, 'w', encoding='utf-8') as f:
            f.write(detail_response.text)
        continue

    for card in cards:
        start = time.perf_counter() # старт замера времени для объявления
        time.sleep(random.uniform(1.5, 3))
        try:
            detail_url = card.find(class_='a-card__link').get('href')
            detail_url = f'https://kolesa.kz{detail_url}'
        except:
            log.error(f'Ошибка получения ссылки card = {card} | страница {page} | {brand.upper()}')
            continue
        try:
            try:
                detail_response = session.get(detail_url)
                log.info(f'Открыто объявление {detail_url}')
            except Exception as e:
                log.error(f'Ошибка открытия объявления {detail_url}')
                log.error(e)
                continue

            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')

            kolesa_id = detail_url.replace('https://kolesa.kz/a/show/', '').split('?')[0]

            debug_filename = f'for_debug_{kolesa_id}.html'

            title = detail_soup.find('h1')
            # https://stackoverflow.com/questions/48778818/get-itemprop-with-beautifulsoup
            car_brand = title.find('span', itemprop='brand').text.strip()
            car_model = title.find('span', itemprop='name').text.strip()
            car_year = title.find(class_='year').text.strip()

            price = detail_soup.find(class_='offer__price').text.replace('₸', '').replace('\xa0', '').strip()

            params = detail_soup.find(class_='offer__parameters')

            try:
                city = detail_soup.find('dd', attrs={'data-test': 'Город'}).text
            except:
                city = None
                log.warning(f'Отсутствует город для объявления {detail_url}')

            try:
                generation = detail_soup.find('dt', title='Поколение').find_next('dd').text
            except:
                generation = None
                log.warning(f'Отсутствует поколение для объявления {detail_url}')
            
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
            
            try:
                color = detail_soup.find('dt', title='Цвет').find_next('dd').text
            except:
                log.warning(f'Отсутствует цвет для объявления {detail_url}')
                color = None

            kz_registration = detail_soup.find('dt', title='Растаможен в Казахстане').find_next('dd').text

            # не работает
            # try:
            #     description_text = detail_soup.find('div', attrs={'data-test': 'description-text'}).text
            # except Exception as e:
            #     log.warning(f'Отсутствует описание для объявления {detail_url}')
            #     log.error(e)
            #     description_text = None

            # try:
            #     publish_info = detail_soup.find(class_='offer__info-views').text
            # except:
            #     log.warning(f'Отсутствуют данные о публикации для объявления {detail_url}')
            #     publish_info = None

            # получение фото
            try:
                imgs_count = len(detail_soup.find(class_='gallery__thumbs-list').find_all(class_='gallery__thumb')) # количество фото
                img_url = detail_soup.find(class_='gallery__main').find('img').get('src')
                # https://www.centron.de/en/tutorial/get-file-extension-in-python-step-by-step-guide/
                extension = Path(img_url).suffix
            except:
                log.error(f'Ошибка получение ссылки для фото для объявления {detail_url} | пропускаем')
                with open(debug_filename, 'w', encoding='utf-8') as f:
                    f.write(detail_response.text)
                continue

            try:
                time.sleep(random.uniform(0.5, 1.5))
                # https://stackoverflow.com/questions/30229231/python-save-image-from-url
                img_data = session.get(img_url).content
                img_filename = f'{kolesa_id}{extension}'
                with open(Path(f'data/images/{img_filename}'), 'wb') as handler:
                    handler.write(img_data)
            except:
                log.error(f'Ошибка загрузки и сохранения фото для объявления {detail_url} | пропускаем')
                with open(debug_filename, 'w', encoding='utf-8') as f:
                    f.write(detail_response.text)
                continue

            row = {
                'kolesa_id': kolesa_id,
                'parsed_at': datetime.now(timezone(timedelta(hours=3))), # https://younglinux.info/datetime/datetime
                'brand': car_brand,
                'model': car_model,
                'generation': generation,
                'year': car_year,
                'city': city,
                'body_type': body_type,
                'fuel_type': fuel_type,
                'engine_volume': engine_volume,
                'mileage': mileage,
                'transmission': transmission,
                'drive_type': drive_type,
                'steering_wheel': steering_wheel,
                'color': color,
                'kz_registration': kz_registration,
                # 'description': description_text,
                # 'publish_info': publish_info,
                'imgs_count': imgs_count,
                'price': price,
                'img_filename': img_filename
            }

            rows.append(row)
            finish = time.perf_counter()
            res = finish - start
            log.info(f'Получено объявление {car_brand} {car_model} {price}₸. id = {kolesa_id} | затрачено {res} сек.')
        except Exception as e:
            log.error(f'Неизвестная ошибка получения объявления {detail_url}')
            log.error(e)
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(detail_response.text)

    page_finish = time.perf_counter()
    page_res = page_finish - page_start
    log.info(f'Страница {page} (для {brand.upper()}) собрана | затрачено {page_res} сек.')

    time.sleep(random.uniform(2, 5))

total_finish = time.perf_counter()
total_res = total_finish - total_start

if len(rows) > 0:
    df = pd.DataFrame(rows).to_csv(Path(f'data/raw/{output_filename}.csv'), index=False)

    log.info(f'Датасет {output_filename}.csv для {brand.upper()}, страницы {page0} - {page1} собран | затрачено {total_res} сек.')
