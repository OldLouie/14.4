import telebot
from telebot import types
from telebot.storage import StateMemoryStorage
from config import (API_TOKEN, MEDIUM_GAME_PRICE, MEDIUM_GAME_DESCRIPTION,
                    BIG_GAME_PRICE, BIG_GAME_DESCRIPTION,
                    VERY_BIG_GAME_PRICE, VERY_BIG_GAME_DESCRIPTION,
                    OTHER_OFFERS_PRICE, OTHER_OFFERS_DESCRIPTION)
from PIL import Image
import sqlite3

bot = telebot.TeleBot(API_TOKEN, parse_mode=None)
storage = StateMemoryStorage()

# Клавиатуры
kb1 = types.ReplyKeyboardMarkup(resize_keyboard=True)
button1 = types.KeyboardButton(text='Рассчитать')
button2 = types.KeyboardButton(text='Информация')
button3 = types.KeyboardButton(text='Купить')
button4 = types.KeyboardButton(text='О нас')
kb1.add(button1, button2).add(button3, button4)


def buy_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Продукт № 1", callback_data="medium_game"))
    markup.add(types.InlineKeyboardButton("Продукт № 2", callback_data="big_game"))
    markup.add(types.InlineKeyboardButton("Продукт № 3", callback_data="very_big_game"))
    markup.add(types.InlineKeyboardButton("Продукт № 4", callback_data="other_offers"))
    return markup


def resize_image(input_path, output_path, size):
    with Image.open(input_path) as img:
        img.thumbnail(size)
        img.save(output_path)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я бот, помогающий твоему здоровью.", reply_markup=kb1)


@bot.message_handler(func=lambda message: message.text == "Информация")
def info(message):
    bot.send_message(message.chat.id,
                     "Расчет по формуле Миффлина-Сан Жеора:\n"
                     "10 х вес (кг) + 6,25 x рост (см) – 5 х возраст (г) - 161 (для женщин)\n"
                     "10 х вес (кг) + 6,25 x рост (см) – 5 х возраст (г) + 5 (для мужчин)")


@bot.message_handler(func=lambda message: message.text == "Рассчитать")
def schet(message):
    bot.send_message(message.chat.id, 'Выберите ваш пол:',
                     reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add('Мужчина', 'Женщина'))
    bot.register_next_step_handler(message, process_gender)


def process_gender(message):
    gender = message.text
    if gender not in ['Мужчина', 'Женщина']:
        bot.send_message(message.chat.id, "Пожалуйста, выберите 'Мужчина' или 'Женщина'.")
        return
    bot.send_message(message.chat.id, 'Введите свой возраст:')
    bot.register_next_step_handler(message, lambda msg: process_age(msg, gender))


def process_age(message, gender):
    age = int(message.text)
    bot.send_message(message.chat.id, 'Введите свой рост (в см):')
    bot.register_next_step_handler(message, lambda msg: process_growth(msg, age, gender))


def process_growth(message, age, gender):
    growth = int(message.text)
    bot.send_message(message.chat.id, 'Введите свой вес (в кг):')
    bot.register_next_step_handler(message, lambda msg: send_calories(msg, age, growth, gender))


def send_calories(message, age, growth, gender):
    weight = int(message.text)

    if gender == 'Мужчина':
        calories = 10 * weight + 6.25 * growth - 5 * age + 5
    else:  # Женщина
        calories = 10 * weight + 6.25 * growth - 5 * age - 161

    bot.send_message(message.chat.id, f"Ваша дневная норма калорий: {calories} ккал")


@bot.message_handler(func=lambda message: message.text == "Купить")
def buy(message):
    bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=buy_keyboard())


@bot.callback_query_handler(func=lambda call: call.data in ["medium_game", "big_game", "very_big_game", "other_offers"])
def handle_buy_option(call):
    product_info = {
        "medium_game": (MEDIUM_GAME_PRICE, MEDIUM_GAME_DESCRIPTION, 'картинка 1.jpg'),
        "big_game": (BIG_GAME_PRICE, BIG_GAME_DESCRIPTION, 'картинка 2.jpg'),
        "very_big_game": (VERY_BIG_GAME_PRICE, VERY_BIG_GAME_DESCRIPTION, 'картинка 3.jpg'),
        "other_offers": (OTHER_OFFERS_PRICE, OTHER_OFFERS_DESCRIPTION, 'картинка 4.jpg')
    }

    price, description, image_path = product_info[call.data]

    resized_image_path = f"resized_{image_path}"
    resize_image(image_path, resized_image_path, (800, 800))

    # Отправляем изображение товара
    with open(image_path, 'rb') as photo:
        bot.send_photo(call.message.chat.id, photo)

    # Отправляем информацию о продукте и цену
    bot.send_message(call.message.chat.id,
                     f"{description}\nЦена: {price} рублей.",
                     reply_markup=types.InlineKeyboardMarkup().add(
                         types.InlineKeyboardButton("Купить", url="https://example.com")))

    bot.answer_callback_query(call.id)  # Убираем спиннер загрузки


@bot.message_handler(func=lambda message: message.text == "О нас")
def about_us(message):
    bot.send_message(message.chat.id,
                     "Мы команда профессионалов, помогающих вам заботиться о своем здоровье и достигать ваших целей!")


@bot.message_handler(func=lambda message: True)
def all_messages(message):
    bot.send_message(message.chat.id, "Введите команду /start, чтобы начать общение.")


# Запуск бота
bot.polling(none_stop=True)
