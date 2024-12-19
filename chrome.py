import asyncio
import os
import pickle
import random
import time
from typing import Any, List, Self, Union

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from telegram import InputMediaPhoto
from urllib3.exceptions import MaxRetryError
from webdriver_manager.chrome import ChromeDriverManager

from const import FONARTO_XT_PATH, TELEGRAM_BOT_API_TOKEN_DEBUG
from functions import edit_image
from telegram_bot import TelegramBot


class Chrome:
    path: str = ChromeDriverManager().install()
    telegram_bot: TelegramBot = TelegramBot(TELEGRAM_BOT_API_TOKEN_DEBUG)
    windows: List[Union[Self, Any]] = []

    def __new__(cls, *args, **kwargs) -> Self:
        cls.windows.append(
            instance := super().__new__(cls),
        )

        return instance

    def __init__(self: Self, **kwargs) -> None:

        self.options: Options = Options()

        if kwargs.get("headless", False):
            self.options.add_argument("--headless")

        if kwargs.get("disable_gpu", False):
            self.options.add_argument("--disable-gpu")

        if kwargs.get("disable_infobars", False):
            self.options.add_argument("--disable-infobars")

        if kwargs.get("disable_extensions", False):
            self.options.add_argument("--disable-extensions")

        if kwargs.get("start_maximized", False):
            self.options.add_argument("start-maximized")

        if kwargs.get("no_sandbox", False):
            self.options.add_argument("--no-sandbox")

        if kwargs.get("incognito", False):
            self.options.add_argument("--incognito")

        if kwargs.get("tor", False):
            self.options.add_argument("--proxy-server=socks4://127.0.0.1:9050")

        if kwargs.get("block_notifications", False):
            self.options.add_experimental_option(
                "prefs",
                {
                    "profile.default_content_setting_values.notifications": 1,
                },
            )

        self.service: Service = Service(Chrome.path)

        self.driver: webdriver.Chrome = webdriver.Chrome(
            service=self.service,
            options=self.options,
        )

        if cookies_file := kwargs.get("cookies_file", None):
            if site_url := kwargs.get("site_url", None):
                self.driver.get(site_url)
                time.sleep(5 + random.random())

                if os.path.exists(cookies_file):
                    cookies = pickle.load(open(cookies_file, "rb"))

                    for cookie in cookies:
                        self.driver.add_cookie(cookie)

    @classmethod
    def report(cls, msg: str) -> None:
        screenshots: List[bytes] = []

        for window in cls.windows:
            if (
                not isinstance(window, Chrome)
                and hasattr(window, "username")
                and window.username in msg
            ):
                if window.is_alive:
                    screenshot = window.driver.get_screenshot_as_png()
                    screenshot = edit_image(
                        screenshot,
                        text=window.username,
                        font_path=FONARTO_XT_PATH,
                        size=128,
                        position=(50, 25),
                        text_color=(255, 0, 0),
                    )

                    screenshots.append(window.driver.get_screenshot_as_png())

        photos: List[InputMediaPhoto] = [
            InputMediaPhoto(photo, caption=msg) for photo in screenshots
        ]

        asyncio.run(cls.telegram_bot.send_photos(*photos))

    @property
    def is_alive(self: Self):
        """The is_alive property."""
        try:
            self.driver.get_screenshot_as_png()

            return True

        except MaxRetryError:
            pass

        return False
