import os
import threading
from typing import Any, Dict, List

from account import start
from facebook import Facebook

users: List[Dict[str, Any]] = [
    {
        "page_url": "https://www.facebook.com/CityComputerStore",
        "username": "aliabdullah.nasiri",
        "groups": "Math",
        "share_count": 200,
        "comment_count": 250,
        "like_count": 0,
    },
    {
        "page_url": "https://www.facebook.com/profile.php?id=61554947310688",
        "username": "aliabdullah.nasiri",
        "groups": "Math",
        "share_count": 200,
        "comment_count": 250,
        "like_count": 0,
    },
    {
        "page_url": "https://www.facebook.com/profile.php?id=100063642170837",
        "username": "hanif.nasiri.1967",
        "groups": "Math",
        "share_count": 150,
        "comment_count": 200,
        "like_count": 0,
    },
    {
        "page_url": "https://www.facebook.com/PaytakhtMobile",
        "username": "ali.nasiri.20050727",
        "groups": "Math",
        "share_count": 200,
        "comment_count": 150,
        "like_count": 0,
    },
]

threads: List[threading.Thread] = []

for pkl in os.listdir("pkl"):
    threads.append(
        threading.Thread(
            target=start,
            kwargs=dict(
                cookie_file=f"pkl/{pkl}",
                page_url="https://www.facebook.com/PaytakhtMobile",
                username=None,
                groups=["Math"],
                like_count=0,
                share_count=1,
                comment_count=1,
                **dict(
                    headless=True,
                    disable_gpu=True,
                    disable_extensions=True,
                    disable_infobars=True,
                    start_maximized=True,
                    no_sandbox=True,
                    incognito=True,
                    block_notifications=True,
                ),
            ),
        )
    )

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

Facebook.send_report()
