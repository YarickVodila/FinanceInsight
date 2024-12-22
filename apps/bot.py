import asyncio
import json
import logging
from os import getenv
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv
import requests

load_dotenv(override=True)
TOKEN = getenv("BOT_TOKEN")
TEMPLATE_ERROR_MESSAGE = "Ошибка при обработке запроса"
ENDPOINT_URL = getenv("ENDPOINT_URL")

dp = Dispatcher()


async def get_response(query: str) -> str:
    """
    Отправляем запрос на внешний эндпоинт для получения ответа модели.
    """
    try:
        response = await asyncio.to_thread(
            requests.post, ENDPOINT_URL, data=json.dumps({"content": query})
        )
        return response.json().get("response", "")
    except Exception as e:
        logging.error(f"Ошибка при запросе к API: {e}")
        return ""


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Этот хэндлер обрабатывает команду `/start`.
    """
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message()
async def process_question(message: Message) -> None:
    """
    Этот хэндлер получает сообщение и отвечает с использованием внешнего API.
    """
    try:
        await message.bot.send_chat_action(
            chat_id=message.chat.id, action="typing"
        )
    except Exception as e:
        logging.warning(f"Ошибка при отправке chat action: {e}")

    model_answer = await get_response(message.text)
    if not model_answer:
        model_answer = TEMPLATE_ERROR_MESSAGE
    await message.answer(model_answer)


async def main() -> None:
    """
    Главная функция запуска бота.
    """
    bot = Bot(
        token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
