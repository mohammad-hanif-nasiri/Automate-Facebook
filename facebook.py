from typing import Any, Dict, List

from rich.table import Table

from console import console
from functions import send_email


class Facebook:
    report: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def print_report() -> None:
        table: Table = Table(style="cyan bold")

        cols: List[str] = [
            "#",
            "Username",
            "Like",
            "Comment",
            "Share",
            "Friend Requests",
            "Cancelled Friend Requests",
        ]

        for col in cols:
            table.add_column(col)

        rows: List[List[Any]] = []

        for index, (username, data) in enumerate(Facebook.report.items()):
            comment = data.get("comment")
            share = data.get("share")
            like = data.get("like")
            friend_requests = data.get("friend-requests")
            canceled_friend_requests = data.get("canceled-friend-requests")

            row: List[Any] = []

            row.append(index + 1)
            row.append(username)
            row.append(like)
            row.append(comment)
            row.append(share)
            row.append(friend_requests)
            row.append(canceled_friend_requests)

            rows.append(list(map(str, row)))

        for row in rows:
            table.add_row(*row)

        console.print(table)

    @staticmethod
    def send_report():
        if Facebook.report:
            cols: List[str] = [
                "#",
                "Username",
                "Like",
                "Comment",
                "Share",
                "Friend Requests",
                "Cancelled Friend Requests",
            ]
            rows: List[List[Any]] = []

            for index, (username, data) in enumerate(Facebook.report.items()):
                comment = data.get("comment")
                share = data.get("share")
                like = data.get("like")
                friend_requests = data.get("friend-requests")
                canceled_friend_requests = data.get("canceled-friend-requests")

                row = [
                    index + 1,
                    username,
                    like,
                    comment,
                    share,
                    friend_requests,
                    canceled_friend_requests,
                ]
                rows.append(row)

            send_email("Automate - Facebook", cols=cols, rows=rows)
