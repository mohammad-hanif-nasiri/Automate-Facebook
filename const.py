from functions import download_file

TELEGRAM_BOT_API_TOKEN: str = "7989591590:AAHh6kj2ezKKkWW-eLJqVxPZalI6B6flgyM"

FONARTO_REGULAR_URL: str = "https://www.1001fonts.com/download/font/fonarto.regular.ttf"
FONARTO_XT_URL: str = "https://www.1001fonts.com/download/font/fonarto.xt.ttf"

FONARTO_REGULAR_PATH: str = "/tmp/fonarto.regular.ttf"
FONARTO_XT_PATH: str = "/tmp/fonarto.xt.ttf"


download_file(FONARTO_REGULAR_URL, FONARTO_REGULAR_PATH)
download_file(FONARTO_XT_URL, FONARTO_XT_PATH)
