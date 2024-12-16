import os
import re
import threading
from typing import Any, Dict, List

import account
from facebook import Facebook
from functions import kill_main_thread
from main import main


def bg() -> None:
    users: List[Dict[str, Any]] = [
        {
            "page_url": "https://www.facebook.com/CityComputerStore",
            "username": "ahmad.ahmadi.002",
            "credentials": None,
            "groups": ["Math"],
            "share_count": 50,
            "comment_count": 50,
            "like_count": 0,
            "friend_request_count": 50,
            "send_invites": True,
            "telegram_id": 5906633627,
        },
    ]

    files: List[str] = os.listdir("pkl/")
    threads: List[threading.Thread] = []

    for index, user in enumerate(users):
        for file in files:
            if re.match(f"^{user['username']}.*", file):
                threads.append(
                    threading.Thread(
                        target=account.start,
                        kwargs=dict(
                            cookie_file=f"pkl/{file}",
                            credentials=user["credentials"],
                            page_url=user["page_url"],
                            username=user["username"],
                            groups=user["groups"],
                            like_count=user["like_count"],
                            comment_count=user["comment_count"],
                            share_count=user["share_count"],
                            friend_request_count=user["friend_request_count"],
                            telegram_id=user["telegram_id"],
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

    # kill the main thread
    kill_main_thread()


if __name__ == "__main__":
    main(bg)
