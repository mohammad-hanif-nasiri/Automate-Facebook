import os
import re
import threading
from typing import Any, Dict, List

import account
from facebook import Facebook

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

threads: List[threading.Thread] = []

for user, params in users.items():
    for file in os.listdir("pkl/"):
        if re.match(f"^{user}.*", file):
            threads.append(
                threading.Thread(
                    target=account.start,
                    kwargs=dict(
                        cookie_file=f"pkl/{file}",
                        page_url=params["page_url"],
                        username=user,
                        groups=params["groups"],
                        like_count=params["like_count"],
                        share_count=params["share_count"],
                        comment_count=params["comment_count"],
                        **dict(
                            headless=True,
                            disable_gpu=True,
                            disable_infobars=True,
                            disable_extensions=True,
                            start_maximized=True,
                            block_notifications=True,
                            no_sandbox=True,
                            incognito=True,
                            tor=False,
                        ),
                    ),
                )
            )

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

Facebook.send_report()
