from aiogram.dispatcher.filters import Text
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from func import get_item, create_data_dict
from aiogram.dispatcher import FSMContext
from bot import bot, dp
from data_base_class import DataBase


class ForPDAStates(StatesGroup):
    subscribe = State()
    unsubscribe = State()


@dp.message_handler(commands='start', state='*')
async def start(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    sql_query = "INSERT INTO subscribes (userid) VALUES (%s) ON CONFLICT DO NOTHING"
    DataBase().insert(sql_query, user_id)
    kbrd = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True).add('Подписаться', 'Отписаться',
                                                                            'Статус подписки')
    await msg.answer('Приветсиве', reply_markup=kbrd)


@dp.message_handler(Text(equals='Статус подписки'), state='*')
async def status(msg: types.Message, state: FSMContext):
    data = create_data_dict(msg.from_user.id)
    now_subscribes = [data['names'][i] for i in data['subscribe_status'] if data['subscribe_status'][i]]
    now_subscribes_str = ",\n".join(now_subscribes)
    if len(now_subscribes) == 0:
        await msg.answer('Ты не на что не подписан. Может подпишешься на что-нибудь?')
    else:
        await msg.answer(f'Сейчас вы подписаны на категории:\n{now_subscribes_str}')


@dp.message_handler(Text(equals='Подписаться'), state='*')
async def subscribe(msg: types.Message, state: FSMContext):
    await ForPDAStates.subscribe.set()
    data = create_data_dict(msg.from_user.id)
    await state.update_data(data=data)
    now_subscribes = [data['names'][i] for i in data['subscribe_status'] if data['subscribe_status'][i]]
    kbrd = types.InlineKeyboardMarkup(row_width=2)
    for i in data['subscribe_status']:
        if not data['subscribe_status'][i]:
            kbrd.add(data['btns'][i])
    if len(now_subscribes) == 14:
        await msg.answer('Ты подписан на всё что можно', reply_markup=kbrd.add(
            types.InlineKeyboardButton('Отписаться', callback_data='unsubscribe')))
    else:
        await msg.answer('Выберите категорию', reply_markup=kbrd)


@dp.message_handler(Text(equals='Отписаться'), state='*')
async def unsubscribe(msg: types.Message, state: FSMContext):
    await ForPDAStates.unsubscribe.set()
    data = create_data_dict(msg.from_user.id)
    await state.update_data(data=data)
    now_subscribes = [data['names'][i] for i in data['subscribe_status'] if data['subscribe_status'][i]]
    kbrd = types.InlineKeyboardMarkup(row_width=2)
    for i in data['subscribe_status']:
        if data['subscribe_status'][i]:
            kbrd.add(data['btns'][i])
    if len(now_subscribes) == 0:
        for i in data['btns']:
            kbrd.add(data['btns'][i])
        await msg.answer('Ты не на что не подписан. Может подпишешься на что-нибудь?')
        await ForPDAStates.subscribe.set()
        await msg.answer('Выберите категорию', reply_markup=kbrd)
    else:
        await msg.answer('Выберите категорию', reply_markup=kbrd)


@dp.callback_query_handler(state=ForPDAStates.subscribe)
async def subscribe_call(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(category=call.data)
    data = await state.get_data()
    all_subscribe = True
    kbrd = types.InlineKeyboardMarkup(row_width=2)
    itemid = get_item(data['urls'][data['category']])
    DataBase().update('subscribes', data['category'], itemid, call.from_user.id)
    data['subscribe_status'][data['category']] = itemid
    await call.message.answer(f'Вы подписались на категорию {data["names"][data["category"]]}')
    for i in data['subscribe_status']:
        if not data['subscribe_status'][i]:
            all_subscribe = False
            kbrd.add(data['btns'][i])
    if all_subscribe:
        await call.message.answer('Ты подписан на всё что можно')
    else:
        await call.message.answer('Выбери категорию на которую ты хочешь подписаться', reply_markup=kbrd)
    await state.update_data(data=data)
    await call.answer()


@dp.callback_query_handler(state=ForPDAStates.unsubscribe)
async def unsubscribe_call(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(category=call.data)
    data = await state.get_data()
    no_subscribe = True
    kbrd = types.InlineKeyboardMarkup(row_width=2)
    DataBase().update('subscribes', data['category'], '', call.from_user.id)
    data['subscribe_status'][data['category']] = ''
    await call.message.answer(f'Вы подписались на категорию {data["names"][data["category"]]}')
    for i in data['subscribe_status']:
        if data['subscribe_status'][i]:
            no_subscribe = False
            kbrd.add(data['btns'][i])
    if no_subscribe:
        await call.message.answer('Ты не подписан ни на одну категорию')
    else:
        await call.message.answer('Выбери категорию от которой ты хочешь отписаться', reply_markup=kbrd)
    await state.update_data(data=data)
    await call.answer()
