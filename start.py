import os
import re
import threading
from typing import Any, Dict, List

from account import start
from facebook import Facebook

users: List[Dict[str, Any]] = [
    {
        "page_url": "https://www.facebook.com/CityComputerStore",
        "username": "aliabdullah.nasiri",
        "groups": ["Math"],
        "share_count": 200,
        "comment_count": 250,
        "like_count": 0,
    },
    {
        "page_url": "https://www.facebook.com/profile.php?id=61554947310688",
        "username": "aliabdullah.nasiri",
        "groups": ["Math"],
        "share_count": 200,
        "comment_count": 250,
        "like_count": 0,
    },
    {
        "page_url": "https://www.facebook.com/profile.php?id=100063642170837",
        "username": "hanif.nasiri.1967",
        "groups": ["Math"],
        "share_count": 200,
        "comment_count": 250,
        "like_count": 0,
    },
    {
        "page_url": "https://www.facebook.com/PaytakhtMobile",
        "username": "ali.nasiri.20050727",
        "groups": ["Math"],
        "share_count": 200,
        "comment_count": 250,
        "like_count": 0,
    },
]

files: List[str] = os.listdir("pkl/")
threads: List[threading.Thread] = []

for index, user in enumerate(users):
    for file in files:
        if re.match(f"^{user['username']}.*", file):
            threads.append(
                threading.Thread(
                    target=start,
                    kwargs=dict(
                        cookie_file=f"pkl/{file}",
                        page_url=user["page_url"],
                        username=user["username"],
                        groups=user["groups"],
                        like_count=user["like_count"],
                        comment_count=user["comment_count"],
                        share_count=user["share_count"],
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
