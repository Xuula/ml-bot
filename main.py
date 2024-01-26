from aiogram import Bot, types
from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.types import KeyboardButton
from aiogram.types.input_file import BufferedInputFile
from aiogram.filters.state import State, StatesGroup, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

from database import Database
db = Database()

from models import Models
models = Models()

class Payment(StatesGroup):
    awaiting_for_token_amount = State()

class Processing(StatesGroup):
    model_selection = State()
    document_input = State()


dp = Dispatcher(storage=MemoryStorage())

TOKEN = '6673327622:AAErPzNNhGsHwkaKFnKLpjUt3mJxpMTp5XI'

menu_buttons = []
menu_buttons.append(KeyboardButton(text='/help'))
menu_buttons.append(KeyboardButton(text='/pay'))
menu_buttons.append(KeyboardButton(text='/balance'))
menu_buttons.append(KeyboardButton(text='/process'))
menu_buttons = types.ReplyKeyboardMarkup(resize_keyboard= True, keyboard = [menu_buttons])
async def help(message):
    global menu_buttons
    await message.answer("Команды: ", reply_markup=menu_buttons)


@dp.message(CommandStart())
async def command_start_handler(message):
    SG.menu.set()
    await help(message)

def get_tokens_and_create_user(user):
    if db.user_exists(user):
        return db.get_tokens(user)
    else:
        db.create_user(user)
        return 0

@dp.message(StateFilter(None), Command('balance'))
async def cmd_balance(message):
    user = message.from_user.id
    balance = get_tokens_and_create_user(user)
    await message.answer(f'Ваш баланс - {balance} токенов.')

@dp.message(StateFilter(None), Command('pay'))
async def cmd_pay(message, state):
    user = message.from_user.id
    balance = get_tokens_and_create_user(user)
    await message.answer(f'Ваш баланс - {balance} токенов.')
    await message.answer('Введите количество токенов для пополнениея:')
    await state.set_state(Payment.awaiting_for_token_amount);

@dp.message(StateFilter(Payment.awaiting_for_token_amount))
async def cmd_pay(message, state):
    user = message.from_user.id
    balance = get_tokens_and_create_user(user);

    if not message.text.isdigit():
        await message.answer('Неверное количество токенов. Введите число:')
        return
    amount = int(message.text)
    if amount < 1:
        await message.answer('Неверное количество токенов. Введите количество токенов для пополнения:')
        return 
    db.set_tokens(user, balance + amount)
    await message.answer('Пополнение успешно')
    await state.set_state(None)


@dp.message(StateFilter(None), Command('process'))
async def cmd_process(message, state):
    user = message.from_user.id
    balance = get_tokens_and_create_user(user)
    if balance < 200:
        await message.answer(f'Ваш баланс - {balance} токенов, а для обработки документа требуется 100 токенов.')
        return
        
    buttons = []
    for model in models.get_models():
        buttons.append(KeyboardButton(text=model))
    markup = types.ReplyKeyboardMarkup(resize_keyboard= True, keyboard = [buttons])
    await message.answer("Выберите модель:", reply_markup=markup)
    await state.set_state(Processing.model_selection);

@dp.message(StateFilter(Processing.model_selection))
async def select_model(message, state):    
    global menu_buttons
    if not models.is_correct_model(message.text):
        await message.answer('Вы не выбрали модель из списка предложенных.')
        await state.set_state(None);
        return
    await state.update_data(chosen_model = message.text);
    await message.answer('Прикрепите к сообщению файл, который хотите обработать. Он должен быть в формате csv,'
                        ' и в нём должен быть столбец с названием \'Product Title\'.', reply_markup = menu_buttons)
    await state.set_state(Processing.document_input);

@dp.message(StateFilter(Processing.document_input))
async def get_document(message, state):
    global bot
    if message.content_type == types.ContentType.DOCUMENT:
        document_id = message.document.file_id
        file_info = await bot.get_file(document_id)
        file_path = file_info.file_path

        binary = await bot.download_file(file_path)

        document = models.create_document(binary)

        if not document.load():
            await message.answer("Документ не подходит - скорее всего, он не формата csv.")
            await state.set_state(None);
            return
        
        await message.answer("Всё хорошо.")

        user = message.from_user.id
        balance = get_tokens_and_create_user(user)

        db.set_tokens(user, balance - 200)

        chosen = await state.get_data()
        result_data = document.process(chosen['chosen_model'])
        print(message.chat.id)
        result_file = BufferedInputFile(result_data, filename='result.csv')
        await bot.send_document(message.chat.id, result_file)
        await state.set_state(None);
            
    else:
        await message.answer("Прикрепите к сообщению документ.")


@dp.message(StateFilter(None))
async def cmd_help(message):
    await help(message)


async def main() :
    global bot
    await dp.start_polling(bot)


bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
asyncio.run(main())