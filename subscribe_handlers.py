from aiogram import types, Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from func import get_item, create_data_dict
import aiogram.utils.markdown as fmt
from aiogram.dispatcher import FSMContext
from bot import bot, dp
from data_base_class import DataBase


class ForPDAStates(StatesGroup):
    select_mode = State()
    subscribe = State()
    unsubscribe = State()


@dp.message_handler(commands='4', state='*')
async def hello_parser(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    data = create_data_dict(user_id)
    await state.update_data(data=data)

    kbrd = types.InlineKeyboardMarkup()
    kbrd.add(types.InlineKeyboardButton('Подписаться', callback_data='subscribe'))
    kbrd.add(types.InlineKeyboardButton('Отписаться', callback_data='unsubscribe'))

    await msg.answer('Ты можешь подписаться или отписаться от рассылки на 4pda')

    now_subscribes = [data['name'][i] for i in data['subscribe_status'] if data['subscribe_status'][i]]
    if len(now_subscribes) == 0:
        await msg.answer('Сейчас вы не подписаны ни на одну из категорий', reply_markup=kbrd)
    else:
        await msg.answer(f'Сейчас вы подписаны на категории:\n{", ".join(now_subscribes)}', reply_markup=kbrd)

    await ForPDAStates.select_mode.set()

@dp.callback_query_handler(lambda call: call.data == 'subscribe' or call.data == 'unsubscribe', state='*')
async def select_mode(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    kbrd = types.InlineKeyboardMarkup( row_width=3)
    now_subscribes = [data['name'][i] for i in data['subscribe_status'] if data['subscribe_status'][i]]
    if call.data == 'subscribe':
        await ForPDAStates.subscribe.set()
        for i in data['subscribe_status']:
            if not data['subscribe_status'][i]:
                kbrd.add(data['btns'][i])
        if len(now_subscribes) == 5:
            await call.message.answer('Ты подписан на всё что можно', reply_markup=kbrd.add(
                types.InlineKeyboardButton('Отписаться', callback_data='unsubscribe')))
        else:
            await call.message.answer('Выберите категорию', reply_markup=kbrd)
    elif call.data == 'unsubscribe':
        await ForPDAStates.unsubscribe.set()
        for i in data['subscribe_status']:
            if data['subscribe_status'][i]:
                kbrd.add(data['btns'][i])
        if len(now_subscribes) == 0:
            for i in data['btns']:
                kbrd.add(data['btns'][i])
            await call.message.answer('Ты не на что не подписан. Может подпишешься на что-нибудь?')
            await ForPDAStates.subscribe.set()
            await call.message.answer('Выберите категорию', reply_markup=kbrd)
        else:
            await call.message.answer('Выберите категорию', reply_markup=kbrd)

    await call.answer()

@dp.callback_query_handler(state=ForPDAStates.subscribe)
async def subscribe(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(chapter=call.data)
    data = await state.get_data()
    all_subscribe = True
    kbrd = types.InlineKeyboardMarkup(row_width=3)

    if data['chapter'] in data['subscribe_status']:
        itemid = get_item(data['urls'][data['chapter']])
        print(itemid)
        db = DataBase()
        sql_query = f"UPDATE subscribes SET {data['chapter']} = '{itemid}' WHERE userid={call.from_user.id}"
        db.update(sql_query)
        if db.err:
            print(db.err)
        db.close()

        data['subscribe_status'][data['chapter']] = itemid
        await call.message.answer(f'Вы подписались на категорию {data["name"][data["chapter"]]}')

    for i in data['subscribe_status']:
        if not data['subscribe_status'][i]:
            all_subscribe = False
            kbrd.add(data['btns'][i])

    if all_subscribe:
        await call.message.answer('Ты подписан на всё что можно', reply_markup=kbrd.add(
                types.InlineKeyboardButton('Отписаться', callback_data='unsubscribe')))
    else:
        await call.message.answer('Выбери категорию на которую ты хочешь подписаться', reply_markup=kbrd)
    await state.update_data(data=data)
    await call.answer()


@dp.callback_query_handler(state=ForPDAStates.unsubscribe)
async def unsubscribe(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(chapter=call.data)
    data = await state.get_data()
    no_subscribe = True
    kbrd = types.InlineKeyboardMarkup(row_width=5)

    if data['chapter'] in data['subscribe_status']:
        db = DataBase()
        sql_query = f"UPDATE subscribes SET {data['chapter']} = '' WHERE userid={call.from_user.id}"
        db.update(sql_query)
        if db.err:
            print(db.err)
        db.close()
        data['subscribe_status'][data['chapter']] = ''
        await call.message.answer(f'Вы отписались от категории {data["name"][data["chapter"]]}')

    for i in data['subscribe_status']:
        if data['subscribe_status'][i]:
            no_subscribe = False
            kbrd.add(data['btns'][i])

    if no_subscribe:
        for i in data['btns']:
            kbrd.add(data['btns'][i])
        await call.message.answer('Ты не на что не подписан. Может подпишешься на что-нибудь?', reply_markup=kbrd)
        await ForPDAStates.subscribe.set()
    else:
        await call.message.answer('Выбери категорию от которой ты хочешь отписаться', reply_markup=kbrd)
    await state.update_data(data=data)
    await call.answer()
