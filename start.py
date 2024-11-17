import subprocess
import threading
from typing import Dict, List

users: Dict[str, Dict[str, str]] = {
    "aliabdullah.nasiri": {
        "--page-url": "https://www.facebook.com/profile.php?id=61554947310688",
        "--username": "aliabdullah.nasiri",
        "--groups": "Math",
        "--share-count": "150",
        "--comment-count": "100",
        "--like-count": "0",
    },
    "hanif.nasiri.1967": {
        "--page-url": "https://www.facebook.com/profile.php?id=100063642170837",
        "--username": "hanif.nasiri.1967",
        "--groups": "Math",
        "--share-count": "150",
        "--comment-count": "100",
        "--like-count": "0",
    },
}

threads: List[threading.Thread] = []

for user, options in users.items():
    threads.append(
        threading.Thread(
            target=subprocess.run,
            args=(
                ["python3", "facebook.py"]
                + [
                    "--headless",
                    "--disable-gpu",
                    "--disable-infobars",
                    "--disable-extensions",
                    "--start-maximized",
                    "--block-notifications",
                    "--no-sandbox",
                ]
                + ["main"]
                + " ".join([" ".join(option) for option in options.items()]).split(" "),
            ),
        )
    )

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()
