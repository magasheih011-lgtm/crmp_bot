import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

TELEGRAM_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

if not TELEGRAM_BOT_TOKEN or OWNER_ID == 0:
    raise ValueError("Не заданы переменные TG_BOT_TOKEN или OWNER_ID!")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
current_calls = {}

async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗣 Форум Матрёшка РП", url="https://forum.matrp.ru/index.php")
    builder.button(text="✅ Подписаться на канал", url=f"https://t.me/{(await bot.get_me()).username}")
    builder.adjust(1, 1)

    is_sub = await is_subscribed(message.from_user.id)
    if not is_sub:
        await message.answer(
            "👋 Привет! Чтобы видеть обзвоны, подпишись на канал комьюнити.\n"
            "А если хочешь просто на форум — жми кнопку ниже.",
            reply_markup=builder.as_markup()
        )
        return
    await ask_server(message)

async def ask_server(message: types.Message):
    await message.answer("🎮 Напиши номер сервера (от 1 до 34), чтобы увидеть открытые обзвоны:")

@dp.message(F.text)
async def handle_server_input(message: types.Message):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Напиши только число (например: 15).")
        return

    server_num = int(text)
    if server_num < 1 or server_num > 34:
        await message.answer("⚠️ Сервер должен быть от 1 до 34.")
        return

    server_data = current_calls.get(str(server_num))
    if not server_data or not server_data.get("calls"):
        await message.answer(f"❌ На сервере {server_num} сейчас нет открытых обзвонов.\nАдмин скоро обновит данные.")
        return

    calls_text = f"🗣 Открытые обзвоны на сервере {server_num}:\n\n"
    for c in server_data["calls"]:
        calls_text += f"🏛 Организация: {c['org']}\n"
        calls_text += f"👤 Должность: {c['position']}\n"
        if c.get("date"):
            calls_text += f"📅 Дата: {c['date']}\n"
        if c.get("link"):
            calls_text += f"🔗 Ссылка: {c['link']}\n"
        calls_text += "--------------------------\n"

    await message.answer(calls_text)

@dp.message(Command("updatecalls"))
async def cmd_update_calls(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer(
        "Отправь JSON с данными обзвонов следующим сообщением.\n"
        "Пример:\n```json\n{\"15\": {\"calls\": [{\"org\": \"МВД\", \"position\": \"Замнач\", \"date\": \"20.08\"}]}}\n```",
        parse_mode="Markdown"
    )

@dp.message(F.json)
async def handle_json_update(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        new_data = json.loads(message.text)
        global current_calls
        current_calls = new_data
        await message.answer("✅ Данные обзвонов обновлены!")
    except Exception as e:
        await message.answer(f"❌ Ошибка формата JSON: {e}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
