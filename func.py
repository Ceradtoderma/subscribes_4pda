import requests
from bs4 import BeautifulSoup
from data_base_class import DataBase
import asyncio
from bot import bot

import aiogram.utils.markdown as fmt
from aiogram import types
from pprint import pprint
from datetime import datetime, date, time


def create_data_dict(user_id):
    data = dict(subscribe_status={}, btns={})
    data['urls'] = {
        'news_smartphones': 'https://4pda.to/tag/smartphones/',
        'news_notebook': 'https://4pda.to/tag/notebooks/',
        'news_pc': 'https://4pda.to/tag/pc/',
        'news_appliances': 'https://4pda.to/tag/appliances/',
        'news_audio': 'https://4pda.to/tag/audio/',
        'news_monitors': 'https://4pda.to/tag/monitors/',
        'news_games': 'https://4pda.to/games/',
        'reviews_smartphones': 'https://4pda.to/reviews/smartphones/',
        'reviews_tablets': 'https://4pda.to/reviews/tablets/',
        'reviews_smart_watches': 'https://4pda.to/reviews/smart-watches/',
        'reviews_accessories': 'https://4pda.to/reviews/accessories/',
        'reviews_notebooks': 'https://4pda.to/reviews/notebooks/',
        'reviews_audio': 'https://4pda.to/reviews/audio/',
        'all_news': 'https://4pda.to/'
    }

    data['names'] = {
        'news_smartphones': 'Новости/Смартфоны',
        'news_notebook': 'Новости/Ноутбуки',
        'news_pc': 'Новости/ПК',
        'news_appliances': 'Новости/Бытовая техника',
        'news_audio': 'Новости/Аудио',
        'news_monitors': 'Новости/Тв и мониторы',
        'news_games': 'Новости/Игры',
        'reviews_smartphones': 'Обзоры/Смартфоны',
        'reviews_tablets': 'Обзоры/Планшеты',
        'reviews_smart_watches': 'Обзоры/Умные часы',
        'reviews_accessories': 'Обзоры/Аксессуары',
        'reviews_notebooks': 'Обзоры/Ноутбуки',
        'reviews_audio': 'Обзоры/Аудио',
        'all_news': 'Все новости'
    }

    for i in data['urls']:
        data['subscribe_status'][i] = ''
        data['btns'][i] = types.InlineKeyboardButton(data['names'][i], callback_data=i)

    db_data = DataBase().read_one('subscribes', user_id)
    if db_data:
        cnt = 0
        for i in data['subscribe_status']:
            cnt += 1
            data['subscribe_status'][i] = db_data[cnt]
    else:
        sql_query = "INSERT INTO subscribes (userid) VALUES (%s)"
        DataBase().insert(sql_query, user_id)

    return data


def get_row_data(urls):
    row_data = {}
    for url in urls:
        html = requests.get(urls[url]).text
        soup = BeautifulSoup(html, features="html.parser")
        articles = soup.find_all('article', class_='post')
        data = []
        for i in articles:
            try:
                href = i.find('a').get('href')
            except:
                continue
            item_id = i.get('itemid')
            title = i.find('a').get('title')
            try:
                description = i.find('p').text
                if description == '':
                    continue
            except:
                continue
            data.append((description, title, href, item_id))

            if len(data) == 10:
                break
        row_data[url] = data

    return row_data


def get_prev_items(urls, users):
    prev_items = {}
    for user in users:
        userid = user[0]
        prev_items[userid] = {}
        cnt = 0
        for url in urls:
            cnt += 1
            prev_items[userid][url] = user[cnt]
    return prev_items


def select(prev_item, data):
    selected_data = []
    for i in data:
        if i[3] == prev_item:
            break
        else:
            selected_data.append(i)
    selected_data.reverse()
    return selected_data


def get_last_items(row_data):
    last_items = {}
    for i in row_data:
        last_items[i] = row_data[i][0][3]
    return last_items


def update_data_base(users, prev_items, last_items):

    for user in users:
        userid = user[0]
        for category in last_items:
            if prev_items[userid][category]:
                DataBase().update('subscribes', category, last_items[category], userid)


def get_item(url):
    articles = BeautifulSoup(requests.get(url).text, features="html.parser").find_all('article', class_='post')
    if articles[0].find('p').text:
        return articles[0].get('itemid')
    else:
        return articles[1].get('itemid')


async def send_news(wait_for):
    while True:
        await asyncio.sleep(wait_for)
        urls = {
            'news_smartphones': 'https://4pda.to/tag/smartphones/',
            'news_notebook': 'https://4pda.to/tag/notebooks/',
            'news_pc': 'https://4pda.to/tag/pc/',
            'news_appliances': 'https://4pda.to/tag/appliances/',
            'news_audio': 'https://4pda.to/tag/audio/',
            'news_monitors': 'https://4pda.to/tag/monitors/',
            'news_games': 'https://4pda.to/games/',
            'reviews_smartphones': 'https://4pda.to/reviews/smartphones/',
            'reviews_tablets': 'https://4pda.to/reviews/tablets/',
            'reviews_smart_watches': 'https://4pda.to/reviews/smart-watches/',
            'reviews_accessories': 'https://4pda.to/reviews/accessories/',
            'reviews_notebooks': 'https://4pda.to/reviews/notebooks/',
            'reviews_audio': 'https://4pda.to/reviews/audio/',
            'all_news': 'https://4pda.to/'
        }
        row_data = get_row_data(urls)
        users = DataBase().read_all('subscribes')
        prev_items = get_prev_items(urls, users)

        pac = make_pac(urls, users, prev_items, row_data)

        print(datetime.utcnow())
        pprint(pac)
        for user in pac:
            for str in pac[user]:
                try:
                    await bot.send_message(user, f'{fmt.hide_link(str[2])}', parse_mode=types.ParseMode.HTML)
                    await bot.send_message(user, f'{str[0]}')
                except Exception as err:
                    print(err)

        last_items = get_last_items(row_data)
        update_data_base(users, prev_items, last_items)


def make_pac(urls, users, prev_items, row_data):
    pac = {}
    for user in users:
        pac[user[0]] = []

    for user in pac:
        for url in urls:
            prev_item = prev_items[user][url]
            if prev_item:
                data = row_data[url]
                selected_data = select(prev_item, data)
                if selected_data:
                    for i in selected_data:
                        pac[user].append(i)
    return pac


def main():
    urls = {
        'news_smartphones': 'https://4pda.to/tag/smartphones/',
        'news_notebook': 'https://4pda.to/tag/notebooks/',
        'news_pc': 'https://4pda.to/tag/pc/',
        'news_appliances': 'https://4pda.to/tag/appliances/',
        'news_audio': 'https://4pda.to/tag/audio/',
        'news_monitors': 'https://4pda.to/tag/monitors/',
        'news_games': 'https://4pda.to/games/',
        'reviews_smartphones': 'https://4pda.to/reviews/smartphones/',
        'reviews_tablets': 'https://4pda.to/reviews/tablets/',
        'reviews_smart_watches': 'https://4pda.to/reviews/smart-watches/',
        'reviews_accessories': 'https://4pda.to/reviews/accessories/',
        'reviews_notebooks': 'https://4pda.to/reviews/notebooks/',
        'reviews_audio': 'https://4pda.to/reviews/audio/',
        'all_news': 'https://4pda.to/'
    }
    for i in urls:
        print(i)
        print(get_item(urls[i]))


if __name__ == '__main__':
    main()
