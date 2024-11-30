import asyncio
import random
from typing import Self, Set, Union

from telegram import Bot, PhotoSize
from telegram._utils.types import FileInput

from logger import logger


class TelegramBot:

    def __init__(self, token: str):
        self.bot: Bot = Bot(token)
        self.token: str = token

    async def send_message(self: Self, text: str) -> None:
        logger.info("Attempting to send message to all chat IDs.")  # Start of method

        for chat_id in await self.chat_ids:
            try:
                logger.info(
                    f"Sending message to chat_id: {chat_id}"
                )  # Info about specific chat_id
                await self.bot.send_message(chat_id, text)  # Send the message
                logger.success(
                    f"<b>Message</b> sent <g>successfully</g> to chat_id: <c>{chat_id}</c>"
                )  # Success
                await asyncio.sleep(2.5 + random.random())  # Throttle the requests
            except Exception as err:
                logger.error(
                    f"<r><b>Failed</b></r> to send message to chat_id: <c>{chat_id}</c>. Error: <r><b>{err}</b></r>"
                )  # Log error
                logger.error(
                    "<y>Skipping</y> this chat ID and continuing with the next."
                )  # Info about fallback

    async def send_photo(
        self: Self, photo: Union[FileInput, PhotoSize], caption: Union[str, None] = None
    ) -> None:
        logger.info("Attempting to send photo to all chat IDs.")  # Start of method

        for chat_id in await self.chat_ids:
            try:
                logger.info(
                    f"<b>Sending</b> photo to chat_id: <c>{chat_id}</c>"
                )  # Info about specific chat_id
                await self.bot.send_photo(chat_id, photo, caption)
                logger.success(
                    f"<b>Photo</b> sent <g>successfully</g> to chat_id: <c>{chat_id}</c>"
                )  # Success
                await asyncio.sleep(2.5 + random.random())  # Throttle the requests
            except Exception as err:
                logger.error(
                    f"<r><b>Failed</b></r> to send <b>photo</b> to chat_id: <c>{chat_id}</c>. Error: <r><b>{err}</b></r>"
                )  # Log error
                logger.error(
                    "<y>Skipping</y> this chat ID and continuing with the next."
                )  # Info about fallback

    @property
    async def chat_ids(self: Self) -> Set[Union[str, int]]:
        ids: Set[Union[str, int]] = set()

        for update in await self.bot.get_updates():
            if update.message and update.message.chat_id:
                ids.add(update.message.chat_id)

        return ids


def main(): ...


if __name__ == "__main__":
    main()  # call the main function
