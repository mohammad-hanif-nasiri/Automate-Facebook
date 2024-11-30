import os
import re
import threading
from typing import Any, Dict, List

import account
from facebook import Facebook

users: Dict[str, Dict[str, Any]] = {
    "aliabdullah.nasiri": {
        "page_url": "https://www.facebook.com/CityComputerStore",
        "groups": "Math",
        "share_count": 200,
        "comment_count": 250,
        "like_count": 0,
    },
    "hanif.nasiri.1967": {
        "page_url": "https://www.facebook.com/profile.php?id=100063642170837",
        "groups": "Math",
        "share_count": 150,
        "comment_count": 200,
        "like_count": 0,
    },
    "ali.nasiri.20050727": {
        "page_url": "https://www.facebook.com/PaytakhtMobile",
        "groups": "Math",
        "share_count": 200,
        "comment_count": 150,
        "like_count": 0,
    },
}

threads: List[threading.Thread] = []

for user, params in users.items():
    for file in os.listdir("pkl/"):
        pass

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

Facebook.send_report()
