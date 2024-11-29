import threading
from typing import Any, Dict, List

from chrome import Chrome
from logger import logger

users: Dict[str, Dict[str, Any]] = {
    "aliabdullah.nasiri": {
        "page_url": "https://www.facebook.com/profile.php?id=61554947310688",
        "groups": "Math",
        "share_count": 150,
        "comment_count": 100,
        "like_count": 0,
    },
    "hanif.nasiri.1967": {
        "page_url": "https://www.facebook.com/profile.php?id=100063642170837",
        "groups": "Math",
        "share_count": 150,
        "comment_count": 100,
        "like_count": 0,
    },
    "ali.nasiri.20050727": {
        "page_url": "https://www.facebook.com/PaytakhtMobile",
        "groups": "Math",
        "share_count": 150,
        "comment_count": 100,
        "like_count": 0,
    },
    "mohammad.hanif.nasiri.1967": {
        "page_url": "https://www.facebook.com/CityComputerStore",
        "groups": "Math",
        "share_count": 150,
        "comment_count": 100,
        "like_count": 0,
    },
}


def start(username: str):
    chrome = Chrome()

    chrome.driver.get("https://facebook.com")
    logger.info(f"User <b>{username}</b> - {chrome.driver.title}")


threads: List[threading.Thread] = []

for user, options in users.items():
    threads.append(threading.Thread(target=start, args=(user,)))

for thread in threads:
    thread.start()
    thread.join()
