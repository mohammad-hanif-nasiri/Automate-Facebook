import os
import re
import threading
from typing import List, Union

import click
from flask import Flask, Response, render_template
from pyngrok import ngrok
from selenium.webdriver.chrome.webdriver import WebDriver

from account import start
from chrome import Chrome
from console import console
from facebook import Facebook
from logger import logger
from login import Login


@click.group()
@click.option(
    "--headless",
    is_flag=True,
    help="Run Chrome in headless mode (without a UI).",
)
@click.option(
    "--disable-gpu",
    is_flag=True,
    help="Disable GPU hardware acceleration.",
)
@click.option(
    "--disable-infobars",
    is_flag=True,
    help="Prevent Chrome from showing infobars.",
)
@click.option(
    "--disable-extensions",
    is_flag=True,
    help="Disable all Chrome extensions.",
)
@click.option(
    "--start-maximized",
    is_flag=True,
    help="Start Chrome with the window maximized.",
)
@click.option(
    "--block-notifications",
    is_flag=True,
    help="Block browser notifications from appearing.",
)
@click.option(
    "--no-sandbox",
    is_flag=True,
    help="Disable the sandbox for all running processes. This is useful when running Chrome in environments that do not support sandboxing, such as certain CI/CD systems or containerized environments.",
)
@click.option(
    "--incognito",
    is_flag=True,
    help="Open in incognito mode.",
)
@click.option(
    "--tor",
    is_flag=True,
    help="Use Tor anonymity network.",
)
def cli(
    headless: bool,
    disable_gpu: bool,
    disable_infobars: bool,
    disable_extensions: bool,
    start_maximized: bool,
    block_notifications: bool,
    no_sandbox: bool,
    incognito: bool,
    tor: bool,
):
    # Log the values of each parameter
    logger.info(f"Headless mode: {headless}")
    logger.info(f"Disable GPU: {disable_gpu}")
    logger.info(f"Disable infobars: {disable_infobars}")
    logger.info(f"Disable extensions: {disable_extensions}")
    logger.info(f"Start maximized: {start_maximized}")
    logger.info(f"Block notifications: {block_notifications}")
    logger.info(f"Sandbox: {no_sandbox}")
    logger.info(f"Incognito: {incognito}")
    logger.info(f"Tor: {tor}")


@cli.command()
@click.option(
    "--page-url",
    type=str,
    help="The URL of the page where you want to like all posts and post comments. This option is required.",
    required=True,
)
@click.option(
    "--username",
    type=str,
    help="The username of the account to be used for the operation.",
)
@click.option(
    "--groups",
    type=str,
    callback=lambda ctx, param, value: value.split(",") if value else None,
    help="Comma-separated list of group names where the post will be shared.",
)
@click.option(
    "--share-count",
    type=int,
    default=5,
    help="Number of times to share the post in groups. Default is 5.",
)
@click.option(
    "--comment-count",
    type=int,
    default=10,
    help="Number of comments to post on each post. Default is 10.",
)
@click.option(
    "--like-count",
    type=int,
    default=50,
    help="Specify the number of posts to like. Default is 50.",
)
@click.option(
    "--friend-request-count",
    type=int,
    default=50,
    help="Specify the number of friend requests to send. Default is 50.",
)
@click.option(
    "--send-invites",
    is_flag=True,
    help="Send invites when this flag is used.",
)
@click.option(
    "--cancel-all-friend-requests",
    is_flag=True,
    help="Send invites when this flag is used.",
)
@click.pass_context
def account(
    ctx: click.core.Context,
    page_url: str,
    username: Union[None, str] = None,
    groups: Union[None, List[str]] = None,
    share_count: int = 5,
    comment_count: int = 50,
    like_count: int = 50,
    friend_request_count: int = 50,
    send_invites: bool = False,
    cancel_all_friend_requests: bool = False,
) -> None:
    """
    Interact with with Facebook account.
    """

    threads: List[threading.Thread] = []

    if os.path.exists("pkl/"):
        for pkl in os.listdir("pkl"):
            if username and not re.match(f"^{username}.*", pkl):
                continue

            threads.append(
                threading.Thread(
                    target=start,
                    kwargs=dict(
                        cookie_file=f"pkl/{pkl}",
                        page_url=page_url,
                        username=username,
                        groups=groups,
                        like_count=like_count,
                        share_count=share_count,
                        comment_count=comment_count,
                        friend_request_count=friend_request_count,
                        send_invites=send_invites,
                        cancel_all_friend_requests=cancel_all_friend_requests,
                        **ctx.parent.params if ctx.parent else {},
                    ),
                )
            )

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    Facebook.send_report()  # send report


@cli.command()
@click.option(
    "-U",
    "--username",
    type=str,
    help="The username or email address for Facebook login. [Optional]",
)
@click.option(
    "-P",
    "--password",
    type=str,
    help="The password associated with the Facebook account. [Optional]",
)
@click.pass_context
def login(
    ctx: click.core.Context,
    username: Union[None, str],
    password: Union[None, str],
) -> None:
    """
    Login into a new account.
    """
    login: Login = Login(**ctx.parent.params if ctx.parent else {})

    login.login(username, password)


def main():
    # get the main thread process identity
    PID: Union[None, int] = threading.main_thread().native_id

    # call the cli function
    cli()

    logger.info(f"<r>Killing</r> Main Thread (PID: <c>{PID}</c>)...")
    if PID is not None:  # check process identity and then kill the process
        os.kill(PID, 9)


if __name__ == "__main__":
    app: Flask = Flask(__name__)

    @app.route("/report")
    def windows():
        return render_template("report.html", report=Facebook.report)

    thread: threading.Thread = threading.Thread(target=main)
    thread.start()

    port: int = 5000

    if token := os.getenv("NGROK_TOKEN"):
        ngrok.set_auth_token(token)
        tunnel = ngrok.connect(f"{port}")  # Open an ngrok tunnel to the port
        logger.info(
            "Public <bold>URL</bold>: <bold><cyan>{}</cyan></bold>".format(
                tunnel.public_url
            )
        )  # Print the public URL

    app.run(port=port)
