import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from groq import Groq
import config

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

client = Groq(api_key=config.GROQ_KEY)

# ===== ДАННЫЕ =====
user_levels = {}
user_xp = {}
user_state = {}
user_lang = {}

# ===== КЛАВИАТУРЫ =====
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💡 Идея"), KeyboardButton(text="💻 Код")],
        [KeyboardButton(text="📚 Задание"), KeyboardButton(text="📊 Уровень")],
        [KeyboardButton(text="📈 Прогресс"), KeyboardButton(text="🔁 Ещё задание")],
        [KeyboardButton(text="🧠 Объяснить"), KeyboardButton(text="🛠 Исправить")]
    ],
    resize_keyboard=True
)

level_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🟢 Новичок")],
        [KeyboardButton(text="🟡 Средний")],
        [KeyboardButton(text="🔴 Продвинутый")]
    ],
    resize_keyboard=True
)

category_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🐍 Python"), KeyboardButton(text="🌐 JS")],
        [KeyboardButton(text="🐘 PHP")]
    ],
    resize_keyboard=True
)

# ===== УРОВЕНЬ ПО XP =====
def get_rank(xp):
    if xp < 50:
        return "Level 1 🐣"
    elif xp < 150:
        return "Level 2 🚀"
    elif xp < 300:
        return "Level 3 🔥"
    elif xp < 500:
        return "Level 4 💻"
    else:
        return "Level 5 🧠"

# ===== AI =====
async def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Ты генерируешь технические задания для IT-проектов. Не представляйся. Не пиши от первого лица. Сразу давай результат."
                },
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile"
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка AI: {e}"

# ===== ГЕНЕРАЦИЯ ЗАДАНИЯ =====
async def generate_task(lang, level):
    prompt = f"""
Сгенерируй практическое задание.

Язык: {lang}
Уровень: {level}

Без решения. Коротко и понятно.
"""
    return await ask_ai(prompt)

# ===== СТАРТ =====
@dp.message(Command("start"))
async def start(message: types.Message):
    user_xp[message.from_user.id] = 0
    await message.answer(
        "👨‍💻 AI Dev Assistant PRO\n\nВыбирай действие 👇",
        reply_markup=main_kb
    )

# ===== УРОВЕНЬ =====
@dp.message(lambda m: m.text == "📊 Уровень")
async def choose_level(message: types.Message):
    await message.answer("Выбери уровень:", reply_markup=level_kb)

@dp.message(lambda m: m.text in ["🟢 Новичок", "🟡 Средний", "🔴 Продвинутый"])
async def set_level(message: types.Message):
    user_levels[message.from_user.id] = message.text
    await message.answer(f"Уровень: {message.text}", reply_markup=main_kb)

# ===== ПРОГРЕСС =====
@dp.message(lambda m: m.text == "📈 Прогресс")
async def progress(message: types.Message):
    xp = user_xp.get(message.from_user.id, 0)
    rank = get_rank(xp)
    await message.answer(f"XP: {xp}\nРанг: {rank}")

# ===== ЗАДАНИЕ =====
@dp.message(lambda m: m.text == "📚 Задание")
async def choose_category(message: types.Message):
    user_state[message.from_user.id] = "choose_lang"
    await message.answer("Выбери язык 👇", reply_markup=category_kb)

@dp.message(lambda m: m.text in ["🐍 Python", "🌐 JS", "🐘 PHP"])
async def send_task(message: types.Message):
    user_id = message.from_user.id

    lang_map = {
        "🐍 Python": "Python",
        "🌐 JS": "JavaScript",
        "🐘 PHP": "PHP"
    }

    lang = lang_map[message.text]
    user_lang[user_id] = lang

    level = user_levels.get(user_id)
    if not level:
        level = random.choice(["🟢 Новичок", "🟡 Средний", "🔴 Продвинутый"])

    task_text = await generate_task(lang, level)

    user_state[user_id] = "task"

    await message.answer(
        f"📌 Задание\n\nЯзык: {lang}\nУровень: {level}\n\n{task_text}\n\nОтправь код 👇",
        reply_markup=main_kb
    )

# ===== ЕЩЁ ЗАДАНИЕ =====
@dp.message(lambda m: m.text == "🔁 Ещё задание")
async def next_task(message: types.Message):
    user_id = message.from_user.id

    lang = user_lang.get(user_id, "Python")
    level = user_levels.get(user_id, "🟢 Новичок")

    task_text = await generate_task(lang, level)

    user_state[user_id] = "task"

    await message.answer(
        f"📌 Новое задание\n\nЯзык: {lang}\nУровень: {level}\n\n{task_text}"
    )

# ===== ИДЕЯ =====
@dp.message(lambda m: m.text == "💡 Идея")
async def idea(message: types.Message):
    result = await ask_ai("""
Сгенерируй идею IT-проекта в формате ТЗ.
Проект для студента специальности "Информационные системы и программирование".

Технологии:
- HTML
- CSS
- JavaScript
- PHP

Ограничения:
- без AI, VR, машинного обучения
- без сложных интеграций
- уровень: средний студент (не слишком просто, но и не сложно)
                          
Требования:
- НЕ повторяй идеи
- придумай оригинальную концепцию
- не используй банальные решения

Структура:
Название проекта
Описание
Цель
Основной функционал (список)
""")
    await message.answer(result)

# ===== КОД =====
@dp.message(lambda m: m.text == "💻 Код")
async def code(message: types.Message):
    user_state[message.from_user.id] = "code"
    await message.answer("Что сгенерировать?")

# ===== ОБЪЯСНИТЬ =====
@dp.message(lambda m: m.text == "🧠 Объяснить")
async def explain(message: types.Message):
    user_state[message.from_user.id] = "explain"
    await message.answer("Отправь код")

# ===== ИСПРАВИТЬ =====
@dp.message(lambda m: m.text == "🛠 Исправить")
async def fix(message: types.Message):
    user_state[message.from_user.id] = "fix"
    await message.answer("Отправь код")

# ===== ОБРАБОТКА =====
@dp.message()
async def handle_all(message: types.Message):
    user_id = message.from_user.id
    state = user_state.get(user_id)

    if state == "code":
        result = await ask_ai(f"Напиши код: {message.text}")
        await message.answer(result)
        user_state[user_id] = None
        return

    if state == "explain":
        result = await ask_ai(f"Объясни код:\n{message.text}")
        await message.answer(result)
        user_state[user_id] = None
        return

    if state == "fix":
        result = await ask_ai(f"""
        Исправь код.

        Всегда считай, что это код, даже если он неполный.

        Сделай:
        1. Исправленный вариант
        2. Короткое объяснение ошибки

        Код:
        {message.text}
        """)
        await message.answer(result)
        user_state[user_id] = None
        return

    if state == "task":
        result = await ask_ai(f"""
Проверь код студента.

1. Ошибки
2. Что улучшить
3. Оценка (1-10)

Код:
{message.text}
""")

        user_xp[user_id] = user_xp.get(user_id, 0) + 10

        await message.answer(result)
        await message.answer(f"✨ +10 XP | Всего: {user_xp[user_id]}")
        user_state[user_id] = None
        return

    await message.answer("Выбери действие 👇")

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())