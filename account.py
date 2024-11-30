import os
import pickle
import random
import re
import threading
import time
import uuid
from typing import Callable, List, Self, Union

import click
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from chrome import Chrome
from console import console
from facebook import Facebook, cli
from functions import get_comments
from logger import logger


class Account(Facebook, Chrome):
    def __init__(self: Self, cookie_file: str, **kwargs) -> None:
        super().__init__(**kwargs)

        self.cookie_file: str = cookie_file

    def __enter__(self: Self) -> Union[Self, None]:
        """
        Opens a Facebook session and loads stored cookies for authentication.

        This method loads the Facebook homepage, injects cookies for user login, and refreshes the page.
        If login is successful, it initializes the report for tracking user actions.

        Returns:
        --------
        Union[Self, None]
            Returns the bot instance if the login is successful; otherwise, None.
        """
        self.driver.get("https://facebook.com")
        time.sleep(5)

        cookies = pickle.load(open(self.cookie_file, "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)

        self.driver.refresh()

        if self.is_logged_in and self.username:
            Facebook.report.setdefault(
                f"{self.username}",
                {
                    "share": 0,
                    "like": 0,
                    "comment": 0,
                    "points": 0,
                },
            )

            return self

    def __exit__(self: Self, exc_type, exc_value, traceback) -> None:
        """
        Cleans up the session by deleting cookies and quitting the WebDriver.

        This method is called automatically when exiting the context. It deletes all cookies from
        the session and closes the browser.

        Parameters:
        -----------
        exc_type : Exception type
            The exception type if an error occurred during the session, otherwise None.

        exc_value : Exception value
            The exception value if an error occurred during the session, otherwise None.

        traceback : Traceback
            The traceback object if an error occurred during the session, otherwise None.

        Returns:
        --------
        None
        """
        self.driver.delete_all_cookies()
        self.driver.quit()

    def scroll_into_view(self: Self, element: WebElement) -> None:
        """
        Scrolls a specified WebElement into view within the browser window.

        This function leverages JavaScript to smoothly scroll the element into view.
        It centers the element vertically and aligns it horizontally based on its
        closest scrollable ancestor.

        Parameters:
        ----------
        element : WebElement
            The web element to be scrolled into view.

        Returns:
        -------
        None
            This function does not return any value.

        Example:
        -------
        ```python
        element = driver.find_element(By.ID, "targetElement")
        scroll_into_view(self, element)
        ```
        """
        self.driver.execute_script(
            """
            const element = arguments[0];

            element.scrollIntoView({
              behavior: 'smooth',
              block: 'center',
              inline: 'nearest'
            });
            """,
            element,
        )

        time.sleep(1)

    @property
    def is_logged_in(self: Self) -> bool:
        """
        Check if the user is logged into Facebook.

        This property accesses the Facebook homepage and checks for the presence of
        an element that indicates the user is logged in. It looks for the profile
        section of the page, which is only visible when a user is authenticated.

        Returns:
        -------
        bool
            True if the user is logged in (i.e., the profile element is found),
            False otherwise.
        """
        if (url := "https://www.facebook.com") != self.driver.current_url:
            self.driver.get(url)
            time.sleep(5)

        try:
            # Example: Check for the presence of the profile picture or the user's name
            self.driver.find_element(By.XPATH, "//div[@aria-label='Your profile']")
            logger.info("User is logged in.")

            return True
        except Exception:
            logger.info("User is not logged in.")

            return False

    @property
    def username(self: Self) -> Union[str, None]:
        """
        Retrieve the username of the logged-in Facebook user.

        This property accesses the Facebook homepage and attempts to locate the
        username by finding the link in the shortcuts section. If successful,
        it returns the username extracted from the link. If unsuccessful,
        it logs an error and returns None.

        Returns:
        -------
        Union[str, None]
            The username of the logged-in user if found; otherwise, None.
        """

        if hasattr(self, "_username"):
            return self._username

        self.driver.get("https://facebook.com")
        time.sleep(5)

        try:
            link = self.driver.find_element(
                By.XPATH, '//div[@aria-label="Shortcuts"]//a'
            )
            if href := link.get_dom_attribute("href"):
                username = href.split("/").pop()
                logger.info(
                    f"Successfully retrieved the user <b>{username!r}</b> information."
                )
                self._username = username
                return username

        except Exception:
            logger.error("<r>Unable</r> to retrieve username!")

        return None

    @property
    def facebook_element(self: Self) -> WebElement:
        """
        Retrieves the Facebook element by its unique ID.

        Returns:
            WebElement: The web element located by its ID, "facebook",
                        enabling interaction or further manipulation.
        """
        return self.driver.find_element(By.ID, "facebook")

    def get_points(self: Self, page_url: str, timeout: int = 5) -> Union[str, None]:
        pass

    def get_screenshot(
        self: Self,
        url: str,
        callback_fun: Union[None, Callable] = None,
        *args,
        **kwargs,
    ) -> bytes:
        self.driver.get(url)
        time.sleep(5)

        if callback_fun:
            callback_fun(*args, **kwargs)

        return self.driver.get_screenshot_as_png()

    def get_screenshot_as_file(
        self: Self,
        url: str,
        callback_fun: Union[None, Callable] = None,
        *args,
        **kwargs,
    ) -> str:
        with open(path := f"/tmp/{uuid.uuid4()}.png", mode="wb") as file:
            file.write(self.get_screenshot(url, callback_fun, *args, **kwargs))

        return path

    def report_share(self: Self, page_url: str, post_url: str, msg: str) -> None: ...

    def get_last_post_url(
        self: Self, page_url: str, timeout: int = 5
    ) -> Union[str, None]:
        if self.driver.current_url != page_url:
            self.driver.get(page_url)
            self.infinite_scroll(scroll_limit=2, delay=2.5)
            time.sleep(5)

        self.driver.execute_script(
            """
            const facebookElement = document.querySelector('#facebook');

            facebookElement.addEventListener("copy", (event) => {
                let value = event.target.value;

                let postLinkElement = document.createElement("post-link");
                postLinkElement.innerHTML = value;

                facebookElement.append(postLinkElement);
            });
            """
        )

        try:
            try:
                copy_button = self.driver.find_element(
                    By.XPATH,
                    "//span[contains(text(), 'Copy')]/ancestor::*[@role='button']",
                )
                self.scroll_into_view(copy_button)
                copy_button.click()
                time.sleep(5)

            except Exception as _:
                # Find the first "Share" button on the page
                share_button = self.driver.find_element(
                    By.XPATH,
                    "//div[@aria-label='Send this to friends or post it on your profile.'][@role='button']",
                )
                self.scroll_into_view(share_button)
                share_button.click()
                time.sleep(5)

                copy_link_button = self.driver.find_element(
                    By.XPATH,
                    "//div[@role='dialog']//span[contains(text(), 'Copy link')]/ancestor::*[@role='button']",
                )
                copy_link_button.click()
                time.sleep(5)

            link = self.driver.find_element(
                By.TAG_NAME,
                "post-link",
            ).text

            if link:
                logger.success(
                    f"User <b>{self.username!r}</b> - Successfully the last post link ({link}) retrieved."
                )

                return link

        except Exception as err:
            console.print(err, style="red bold")

        logger.error(
            f"User <b>{self.username!r}</b> - <r>Unable</r> to get the last post link."
        )

        return self.get_last_post_url(page_url, timeout - 1) if timeout > 0 else None

    def share(
        self: Self, post_url: str, groups: List[str], count: int, timeout: int = 5
    ) -> None:
        self.driver.get(post_url)
        time.sleep(10)

        prefix: str = ""

        try:
            self.driver.find_element(
                By.XPATH,
                "//div[@role='dialog']//span[contains(text(), 'Share')]",
            )
            prefix = "//div[@role='dialog']"
            logger.info(f"User <b>{self.username}</b> - Dialog Found!")
        except Exception as _:
            logger.warning(f"User <b>{self.username}</b> - Dialog Not Found!")
            prefix = ""

        try:
            for group in groups:
                for _ in range(count // len(groups)):
                    share_count = Facebook.report[f"{self.username}"]["share"]
                    if share_count >= count:
                        logger.success(
                            f"User <b>{self.username!r}</b> - <g>Successfully</g> the sharing process completed!"
                        )
                        return

                    logger.info(
                        f"User <b>{self.username!r}</b> - Preparing to share the last post... (Attempt <c>{share_count+1}</c> of <c>{count}</c>)"
                    )

                    # Find the first "Share" button on the page
                    share_button = self.driver.find_element(
                        By.XPATH,
                        f"{prefix}//span[contains(text(), 'Share')]/ancestor::*[@role='button']",
                    )
                    self.scroll_into_view(share_button)
                    share_button.click()
                    time.sleep(5)

                    # Select the "Share to a Group" option
                    share_to_group_button = self.driver.find_element(
                        By.XPATH,
                        f"{prefix}//span[contains(text(), 'Group')]/ancestor::*[@role='button']",
                    )
                    share_to_group_button.click()
                    time.sleep(5)

                    search_input = self.driver.find_element(
                        By.XPATH,
                        f'{prefix}//input[@placeholder="Search for groups"]',
                    )
                    search_input.send_keys(group)
                    time.sleep(5)

                    group_elem = self.driver.find_element(
                        By.XPATH,
                        f"{prefix}//span[contains(text(), '{group}')]/ancestor::*[@role='button']",
                    )
                    group_elem.click()
                    time.sleep(5)

                    post_button = self.driver.find_element(
                        By.XPATH, f"{prefix}//div[@aria-label='Post']"
                    )
                    post_button.click()

                    for _ in range(15):
                        try:
                            self.driver.find_element(
                                By.XPATH,
                                "//span[contains(text(), 'Shared to your group.')]",
                            )
                            logger.success(
                                f"User <b>{self.username!r}</b> - The post was <b><g>successfully</g></b> shared in the group <b>{group!r}</b>."
                            )

                            # Increment share count in report
                            Facebook.report[f"{self.username}"]["share"] += 1

                            break
                        except Exception as _:
                            pass

                        time.sleep(1)

                    try:
                        spans = self.driver.find_elements(
                            By.XPATH,
                            "//div[@role='dialog']//span",
                        )

                        for span in spans:
                            if "You Can't Use This Feature Right Now" in span.text:
                                logger.warning(
                                    f"User <b>{self.username!r}</b> - You"
                                    " <r>can not</r> <b>share</b> the post right now!"
                                )

                                return

                    except Exception as _:
                        pass

        except Exception as _:
            logger.error(
                f"User <b>{self.username!r}</b> - An <r>error</r> occurred during sharing the post!"
            )
            logger.info(
                f"User <b>{self.username!r}</b> - <b>Retrying</b> to share the post."
            )

            if timeout > 0:
                return self.share(
                    post_url,
                    groups,
                    count,
                    timeout - 1,
                )

    def comment(self: Self, post_url: str, count: int = 50, timeout: int = 5) -> None:
        self.driver.get(post_url)
        time.sleep(5)

        # Retrieve comments random comments
        if comments := get_comments():
            try:
                prefix: str = ""

                try:
                    self.driver.find_element(
                        By.XPATH,
                        "//div[@role='dialog']//div[@aria-label='Write a comment…']",
                    )
                    prefix = "//div[@role='dialog']"
                    logger.info(f"User <b>{self.username}</b> - Dialog Found!")
                except Exception as _:
                    logger.warning(f"User <b>{self.username}</b> - Dialog Not Found!")
                    prefix = ""

                textbox: WebElement = self.driver.find_element(
                    By.XPATH,
                    f'{prefix}//div[@aria-label="Write a comment…"]',
                )

                textbox.click()

                for _ in range(count):
                    comment_count = Facebook.report[f"{self.username}"]["comment"]

                    if comment_count >= count:
                        logger.info(
                            f"User <b>{self.username!r}</b> - <b>Completed</b> commenting process."
                        )
                        return

                    textbox.send_keys(text := random.choice(comments))
                    time.sleep(random.random())

                    textbox.send_keys(Keys.ENTER)
                    time.sleep(1.5)

                    while True:
                        try:
                            self.driver.find_element(
                                By.XPATH,
                                "//span[contains(text(), 'Posting...')]",
                            )
                            time.sleep(0.512)
                            continue

                        except Exception as _:
                            try:
                                self.driver.find_element(
                                    By.XPATH,
                                    "//span[contains(text(), 'Unable to post comment.')]",
                                )

                                logger.warning(
                                    f"User <b>{self.username!r}</b> - You <r>can not</r> write <b>comments</b> right now!"
                                )
                                return

                            except Exception as _:
                                logger.success(
                                    f"User <b>{self.username!r}</b> - <g>Successfully</g> posted comment {comment_count+1}/{count}: <b>{text!r}</b>"
                                )

                                # Increment comment count in report
                                Facebook.report[f"{self.username}"]["comment"] += 1

                                break

                    try:
                        spans = self.driver.find_elements(
                            By.XPATH,
                            "//div[@role='dialog']//span",
                        )

                        for span in spans:
                            if (
                                "You Can't Use This Feature Right Now" in span.text
                                or "You can't use this feature at the moment"
                                in span.text
                            ):
                                logger.warning(
                                    f"User <b>{self.username!r}</b> - You <r>can not</r> write <b>comments</b> right now!"
                                )
                                return

                    except Exception as _:
                        pass

            except Exception as _:
                logger.error(
                    f"User <b>{self.username!r}</b> - <r>Failed</r> to locate or interact with comment textbox."
                )
                if timeout > 0:
                    return self.comment(post_url, count, timeout - 1)

        else:
            logger.error("<r>No</r> comments available to post.")

    def start(
        self: Self,
        *,
        page_url: str,
        username: Union[None, str] = None,
        groups: Union[None, List[str]] = None,
        like_count: int = 50,
        comment_count: int = 50,
        share_count: int = 5,
    ):
        Facebook.report[f"{self.username}"]["page_url"] = page_url
        Facebook.report[f"{self.username}"]["points"] = self.get_points(
            page_url, timeout=5
        )

        if username and username != self.username:
            return

        if post_url := self.get_last_post_url(page_url):
            if share_count > 0 and groups:
                self.share(post_url, groups, share_count)

            if comment_count > 0:
                self.comment(post_url, comment_count)

        if like_count > 0:
            pass

        Facebook.print_report()

    def infinite_scroll(
        self: Self,
        element: Union[WebElement, None] = None,
        delay: float = 5,
        scroll_limit: Union[None, int] = None,
        callback: Union[Callable, None] = None,
        *args,
        **kwargs,
    ) -> None:
        """
        Scrolls down a specified web element to load additional content up to a specified limit.

        This method automatically scrolls to the bottom of the provided web element and waits
        for new content to load. It continues scrolling until either the specified number of
        scrolls is reached or no new content is detected.

        Parameters:
        -----------
        element: Union[WebElement, None], optional
            The specific web element to scroll. If not provided, the method defaults to
            finding the Facebook main element by its ID. This should be an instance of a
            Selenium WebElement that contains scrollable content.

        delay: float, optional
            The time to wait (in seconds) after each scroll before checking for new content.
            Default is 5 seconds.

        scroll_limit: Union[None, int], optional
            The maximum number of scrolls to perform. If set to None, the method will continue
            scrolling until no more new content is loaded. Default is None.

        callback: Union[Callable, None], optional
            A function to be executed after each successful scroll. This can be used to perform
            actions such as logging the number of items loaded or any other processing. Default is None.

        *args:
            Additional positional arguments to pass to the callback function.

        **kwargs:
            Additional keyword arguments to pass to the callback function.

        Returns:
        --------
        None
            This method does not return any value. It performs scrolling actions on the specified
            web element and may execute the provided callback function.

        Raises:
        -------
        WebDriverException
            If the Selenium WebDriver encounters an issue while executing the scrolling actions
            or JavaScript commands.

        Example:
        --------
        >>> def my_callback(arg1, kwarg1=None):
        >>>     print(f"Scrolled and loaded new content! Arg1: {arg1}, Kwarg1: {kwarg1}")
        >>>
        >>> element_to_scroll = driver.find_element(By.ID, "scrollable-element-id")  # Example element
        >>> infinite_scroll(element=element_to_scroll, scroll_limit=5, callback=my_callback, "Some value", kwarg1="Some keyword value")
        """

        if not element:
            element = self.facebook_element

        last_height = self.driver.execute_script(
            "return arguments[0].scrollHeight", element
        )

        count = 0  # Initialize scroll count
        while True:
            # Scroll to the bottom of the page
            self.driver.execute_script(
                "window.scrollTo(0, arguments[0].scrollHeight);", element
            )

            # Wait for new content to load
            time.sleep(delay)  # Adjust based on your needs

            # Calculate new height and compare with the last height
            new_height = self.driver.execute_script(
                "return arguments[0].scrollHeight", element
            )
            if new_height == last_height:
                break  # Break the loop if no new content has been loaded

            # Update the last height
            last_height = new_height

            # Execute the callback function
            if callback:
                if (
                    callback(*args, **kwargs) is not None
                ):  # Call the provided callback function
                    break

            # Increment the scroll count and check against the limit
            count += 1
            if scroll_limit is not None and count >= scroll_limit:
                break  # Exit if the scroll limit is reached

        if callback:
            callback(*args, **kwargs)


def start(
    cookie_file: str,
    page_url: str,
    username: Union[None, str] = None,
    groups: Union[None, List[str]] = None,
    like_count: int = 50,
    comment_count: int = 50,
    share_count: int = 5,
    **kwarg,
):
    with Account(cookie_file, **kwarg) as account:
        if account:
            account.start(
                page_url=page_url,
                username=username,
                groups=groups,
                like_count=like_count,
                comment_count=comment_count,
                share_count=share_count,
            )


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
@click.pass_context
def main(
    ctx: click.core.Context,
    page_url: str,
    username: Union[None, str] = None,
    groups: Union[None, List[str]] = None,
    share_count: int = 5,
    comment_count: int = 50,
    like_count: int = 50,
) -> None:

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
                        **ctx.parent.params if ctx.parent else {},
                    ),
                )
            )

    console.print(threads)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    Facebook.send_report()


if __name__ == "__main__":
    cli()
