import aiohttp
from aiogram import Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import json
import os


bot = Bot(token=os.environ['BOT_TOKEN'])
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот, который по названию фильма или сериала поможет найти тебе всю информацию, а также покажет, где можно его посмотреть!")

@dp.message_handler(commands=['help'])
async def send_welcome(message: types.Message):
    await message.reply("Введи название фильма или сериала, и я покажу всю информацию!")

def get_search_link(words, type_search):
    token = os.environ['TMDB_TOKEN']
    link = 'https://api.themoviedb.org/3/search/'+ type_search + '?api_key=' + token + '&language=ru&append_to_response=videos&query='
    for i in range(len(words)):
        link += words[i] + '+'
    return link[:-1]

def get_search_link2(type_search, id):
    token = os.environ['TMDB_TOKEN']
    link = 'https://api.themoviedb.org/3/'+ type_search + '/' + str(id) + '/watch/providers?api_key=' + token + '&language=ru'
    return link

@dp.message_handler()
async def reply_call(message: types.Message):
    text = message.text
    words = text.split(' ')

    keyboard_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Сериал", callback_data='t'+text)], [InlineKeyboardButton(text="Фильм", callback_data='m'+text)]])

    await message.reply(
        'Ищешь сериал или фильм?',
        reply_markup=keyboard_markup
    )

@dp.callback_query_handler()
async def accept_option(query: types.CallbackQuery):
    text = query.data

    words = text[1:].split(' ')
    s = 'tv'
    if text[0] != 't':
        s = 'movie'

    link = get_search_link(words, s)
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as response:

            if response.status != 200:
                await query.message.reply('Что-то пошло не так:( Пожалуйста, повтори свой запрос')
                return

            reply = await response.json()
            res = reply['results']

            if len(res) == 0:
                await query.message.reply('Нет ничего с похожим названием:( Попробуй еще раз!')
                return

            film = res[0]
            mid = film['id']


            link2 = get_search_link2(s, mid)

            async with aiohttp.ClientSession() as session2:
                async with session.get(link2) as response2:

                    if response2.status != 200:
                        await query.message.reply('Что-то пошло не так:( Пожалуйста, повтори свой запрос')
                        return

                    reply2 = await response2.json()
                    film2 = ""

                    obj = 'фильм'
                    if s == 'tv':
                        obj = 'сериал'

                    take = 'RU'

                    if 'RU' not in reply2['results']:
                        take = 'US'
                        if 'US' not in reply2['results']:
                            await query.message.reply('К сожалению, этого ' + obj + 'а нет на русском или английском языке :(')
                            await bot.answer_callback_query(query.id)
                            return
                        else:
                            film2 = reply2['results']['US']['link']

                    else:
                        film2 = reply2['results']['RU']['link']

                    name = ""
                    if "original_title" in film:
                        name = film["original_title"]
                    if "name" in film:
                        name = film["name"]

                    info = ""
                    info += name + '\n'
                    info += 'Описание: ' + film["overview"] + '\n'
                    if "vote_average" in film:
                        info += 'Оценка ' + obj + 'а: ' + str(film["vote_average"]) + '\n'
                    if "origin_country" in film:
                        info += 'Страна ' + obj + 'а: ' + film["origin_country"][0] + '\n'

                    info += 'Посмотреть можно, кликнув на баннер по ссылке ' + film2 + ' (язык = ' + take + ')'

                    if film['poster_path'] is not None:
                        poster_link = 'https://image.tmdb.org/t/p/w500' + film['poster_path']

                        await bot.send_photo(
                            query.message.chat.id,
                            poster_link,
                            caption=info,
                        )

                    else:
                        await query.message.reply(info)

                    await bot.answer_callback_query(query.id)


if __name__ == '__main__':
    executor.start_polling(dp)
