import asyncio
import random
from typing import Any, Dict, List, Self, Set

import requests
from telegram import Bot

from logger import logger


class TelegramBot:

    def __init__(self, token: str):
        self.bot: Bot = Bot(token)

    async def send_message(self: Self, text: str) -> None:
        logger.info("Attempting to send message to all chat IDs.")  # Start of method

        for chat_id in self.chat_ids:
            try:
                logger.info(
                    f"Sending message to chat_id: {chat_id}"
                )  # Info about specific chat_id
                await self.bot.send_message(chat_id, text)  # Send the message
                logger.success(
                    f"Message sent successfully to chat_id: {chat_id}"
                )  # Success
                await asyncio.sleep(2.5 + random.random())  # Throttle the requests
            except Exception as err:
                logger.error(
                    f"Failed to send message to chat_id: {chat_id}. Error: {err}"
                )  # Log error
                logger.error(
                    "Skipping this chat ID and continuing with the next."
                )  # Info about fallback

    @property
    def chat_ids(self: Self) -> Set[str]:
        ids: Set[str] = set()

        response: requests.Response = requests.get(
            f"https://api.telegram.org/bot7989591590:{self.bot.token}/getUpdates"
        )

        if response.status_code == 200:
            data = response.json()

            result: List[Dict[str, Any]] = data.get("result", [])
            ids.update(
                set(map(lambda message: message["message"]["chat"]["id"], result))
            )

        return ids


def main():
    telegram_bot: TelegramBot = TelegramBot(
        "7989591590:AAHh6kj2ezKKkWW-eLJqVxPZalI6B6flgyM"
    )

    asyncio.run(telegram_bot.send_message("Hi"))


if __name__ == "__main__":
    main()  # call the main function
