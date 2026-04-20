import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "8771270282:AAH_jSr_R-b_uVK3RBAzgSzKGmIMkO1iWUI"
GROUP_ID = -1002694002879  # <-- ТВОЯ ГРУППА

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

trips = {}
participants = {}

# --- КНОПКА ---
def get_keyboard(trip_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="👍 Я еду",
            callback_data=f"join_{trip_id}"
        )]
    ])

# --- СОЗДАНИЕ ПОЕЗДКИ ---
@dp.message(Command("trip"))
async def create_trip(message: types.Message):
    trips[message.from_user.id] = {}
    await message.answer("Введите маршрут (например: Вильнюс → Каунас):")

@dp.message()
async def handle_trip(message: types.Message):
    user_id = message.from_user.id

    if user_id not in trips:
        return

    data = trips[user_id]

    if "route" not in data:
        data["route"] = message.text
        await message.answer("Введите дату (DD-MM/DD-MM):")

    elif "date" not in data:
        data["date"] = message.text
        await message.answer("Введите время (HH:MM):")

    elif "time" not in data:
        data["time"] = message.text

        trip_id = str(message.message_id)
        participants[trip_id] = []

        date_obj = datetime.strptime(data["date"], "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d.%m")

        title = f"{data['route']} {formatted_date}"

        # --- СОЗДАЁМ ТЕМУ В ГРУППЕ ---
        topic = await bot.create_forum_topic(
            chat_id=GROUP_ID,
            name=title
        )

        # --- ССЫЛКА НА ТЕМУ ---
        topic_link = f"https://t.me/c/{str(GROUP_ID)[4:]}/{topic.message_thread_id}"

        text = f"""🚗 <b>{title}</b>

📅 {data['date']}
🕒 {data['time']}

👥 Пока никто не записался

💬 <a href="{topic_link}">Обсуждение</a>
"""

        # --- ОТПРАВКА В ТЕМУ ---
        msg = await bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=topic.message_thread_id,
            text=text,
            reply_markup=get_keyboard(trip_id),
            parse_mode="HTML"
        )

        # --- УДАЛЕНИЕ ---
        trip_datetime = datetime.strptime(
            data["date"] + " " + data["time"],
            "%Y-%m-%d %H:%M"
        )

        scheduler.add_job(
            delete_message,
            "date",
            run_date=trip_datetime,
            args=[GROUP_ID, msg.message_id]
        )

        trips.pop(user_id)

# --- КНОПКА "Я ЕДУ" ---
@dp.callback_query(F.data.startswith("join_"))
async def join_trip(callback: types.CallbackQuery):
    trip_id = callback.data.split("_")[1]
    user = callback.from_user

    if user.full_name not in participants[trip_id]:
        participants[trip_id].append(user.full_name)

    names = "\n".join(participants[trip_id])

    new_text = callback.message.text.split("👥")[0] + f"""👥 Участники:
{names}
"""

    await callback.message.edit_text(
        new_text,
        reply_markup=get_keyboard(trip_id),
        parse_mode="HTML"
    )

    await callback.answer("Ты записан ✅")

# --- УДАЛЕНИЕ ---
async def delete_message(chat_id, message_id):
    try:
        await bot.delete_message(chat_id, message_id)
    except:
        pass

# --- ЗАПУСК ---
async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
