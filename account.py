import asyncio
import pickle
import random
import time
import uuid
from typing import Callable, Dict, List, Literal, Self, Union
from selenium.webdriver.chrome.webdriver import WebDriver

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from telegram import InputMediaPhoto
from urllib3.exceptions import ReadTimeoutError

from chrome import Chrome
from const import FONARTO_XT_PATH, TELEGRAM_BOT_API_TOKEN
from exceptions import UserNotLoggedInException
from facebook import Facebook
from functions import edit_image, get_comments
from logger import logger
from login import Login
from telegram_bot import TelegramBot


class Account(Facebook, Chrome):
    def __init__(
        self: Self,
        cookie_file: str,
        credentials: Union[Dict[Literal["username", "password"], str], None] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.cookie_file: str = cookie_file
        self.credentials: Union[
            Dict[Literal["username", "password"], str],
            None,
        ] = credentials
        self.telegram_bot: TelegramBot = TelegramBot(TELEGRAM_BOT_API_TOKEN)

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

        if not (is_logged_in := self.is_logged_in) and self.credentials is not None:
            username: Union[str, None] = self.credentials.get(
                "username"
            )  # get username from credentials dictionary
            password: Union[str, None] = self.credentials.get(
                "password"
            )  # get password from credentials dictionary

            if username and password:  # validate username and password
                # Perform automatically login using the Login static method
                is_logged_in = Login.preform_automatically_login(
                    self.driver, username, password
                )

        if is_logged_in and self.username:
            Facebook.report.setdefault(
                f"{self.username}",
                {
                    "share": 0,
                    "like": 0,
                    "comment": 0,
                    "friend-requests": 0,
                    "canceled-friend-requests": 0,
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

    def check_feature(self: Self, driver: Union[WebDriver, None] = None) -> bool:

        if driver is None:
            driver = self.driver

        messages: List[str] = [
            "You Can't Use This Feature Right Now",
            "You can't use this feature at the moment",
        ]

        try:
            spans: List[WebElement] = driver.find_elements(
                By.XPATH, "//div[@role='dialog']//span"
            )

            for span in spans:
                for message in messages:
                    if message in span.text:
                        logger.warning(f"User <b>{self.username}</b> - {message}")

                        return False

        except Exception:
            pass

        return True

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
    def username(self: Self) -> str:
        """
        Retrieves the username of the currently logged-in Facebook user.

        This method attempts to fetch the username by navigating to the Facebook homepage
        and extracting it from a shortcut link. If the username is already cached as
        an instance attribute `_username`, it returns the cached value.

        Process:
            1. Checks if `_username` is already available and returns it.
            2. Navigates to the Facebook homepage using the web driver.
            3. Searches for the shortcut link element containing the username.
            4. Extracts the username from the link's `href` attribute.
            5. Logs the retrieved username and caches it in `_username`.

        Logging:
            - Logs a success message if the username is retrieved successfully.
            - Logs an error message if username retrieval fails.

        Exceptions:
            - Raises `UserNotLoggedInException` if the user is not logged in or if
              the username cannot be determined.

        Returns:
            str: The username of the logged-in Facebook user.

        Raises:
            UserNotLoggedInException: If the username could not be retrieved, likely
            because the user is not logged in.

        Example:
            >>> user = FacebookBot(driver)
            >>> print(user.username)
            Successfully retrieved the user 'john_doe' information.
            'john_doe'

        Notes:
            - Ensure that the driver is authenticated and navigable to Facebook.
            - The method assumes that the user shortcuts are accessible on the homepage.

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
                username = self._username = href.split("/").pop()

                logger.info(
                    f"Successfully retrieved the user <b>{username!r}</b> information."
                )

                return username

        except Exception:
            logger.error("<r>Unable</r> to retrieve username!")

        raise UserNotLoggedInException()

    @property
    def facebook_element(self: Self) -> WebElement:
        """
        Retrieves the Facebook element by its unique ID.

        Returns:
            WebElement: The web element located by its ID, "facebook",
                        enabling interaction or further manipulation.
        """
        return self.driver.find_element(By.ID, "facebook")

    def get_screenshot(
        self: Self,
        url: str,
        callback_func: Union[None, Callable] = None,
        timeout: int = 5,
        /,
        **kwargs,
    ) -> Union[None, bytes]:
        self.driver.get(url)
        time.sleep(5)

        if callback_func:
            callback_func(**kwargs)

        try:
            return self.driver.get_screenshot_as_png()
        except Exception:
            if timeout > 0:
                time.sleep(5)
                return self.get_screenshot(url, callback_func, timeout - 1)

    def get_screenshot_as_file(
        self: Self,
        url: str,
        callback_fun: Union[None, Callable] = None,
        *args,
        **kwargs,
    ) -> str:
        with open(path := f"/tmp/{uuid.uuid4()}.png", mode="wb") as file:
            screenshot = self.get_screenshot(url, callback_fun, *args, **kwargs)
            if screenshot:
                file.write(screenshot)

        return path

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

            except Exception:
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

        except Exception:
            pass

        logger.error(
            f"User <b>{self.username!r}</b> - <r>Unable</r> to get the last post link."
        )

        return self.get_last_post_url(page_url, timeout - 1) if timeout > 0 else None

    def share(
        self: Self, post_url: str, groups: List[str], count: int, timeout: int = 5
    ) -> None:
        self.driver.get(post_url)
        time.sleep(5)

        prefix: str = self.get_selectors_prefix(
            suffix="//span[contains(text(), 'Share')]/ancestor::*[@role='button']"
        )

        try:
            for group in groups:
                for _ in range(count // len(groups)):
                    share_count: int = Facebook.report[self.username]["share"]

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
                    time.sleep(2.5)

                    # Select the "Share to a Group" option
                    share_to_group_button = self.driver.find_element(
                        By.XPATH,
                        f"{prefix}//span[contains(text(), 'Group')]/ancestor::*[@role='button']",
                    )
                    share_to_group_button.click()
                    time.sleep(2.5)

                    search_input = self.driver.find_element(
                        By.XPATH,
                        f'{prefix}//input[@placeholder="Search for groups"]',
                    )
                    search_input.send_keys(group)
                    time.sleep(2.5)

                    group_elem = self.driver.find_element(
                        By.XPATH,
                        f"{prefix}//span[contains(text(), '{group}')]/ancestor::*[@role='button']",
                    )
                    group_elem.click()
                    time.sleep(2.5)

                    post_button = self.driver.find_element(
                        By.XPATH, f"{prefix}//div[@aria-label='Post']"
                    )
                    post_button.click()

                    while True:
                        try:
                            self.driver.find_element(
                                By.XPATH,
                                "//span[contains(text(), 'Shared to your group.')]",
                            )
                            logger.success(
                                f"User <b>{self.username!r}</b> - The post was <b><g>successfully</g></b> shared in the group <b>{group!r}</b>."
                            )

                            # Increment share count in report
                            Facebook.report[self.username]["share"] += 1

                            break
                        except Exception:
                            ...

                        time.sleep(0.512)

                    if self.check_feature() is False:
                        return

        except Exception:
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
                prefix: str = self.get_selectors_prefix(
                    suffix="//span[contains(text(), 'Share')]/ancestor::*[@role='button']"
                )

                textbox: WebElement = self.driver.find_element(
                    By.XPATH,
                    f'{prefix}//div[@aria-label="Write a comment…" or contains(@aria-label, "Comment as") and @role="textbox"]',
                )

                textbox.click()

                for _ in range(count):
                    comment_count: int = Facebook.report[self.username]["comment"]

                    if comment_count >= count:
                        logger.info(
                            f"User <b>{self.username!r}</b> - <b>Completed</b> commenting process."
                        )
                        return

                    textbox.send_keys(text := random.choice(comments))
                    time.sleep(random.random())

                    textbox.send_keys(Keys.ENTER)

                    while True:
                        try:
                            self.driver.find_element(
                                By.XPATH,
                                "//span[contains(text(), 'Posting...')]",
                            )
                            time.sleep(0.512)

                            continue

                        except Exception:
                            try:
                                self.driver.find_element(
                                    By.XPATH,
                                    "//span[contains(text(), 'Unable to post comment.')]",
                                )

                                logger.warning(
                                    f"User <b>{self.username!r}</b> - You <r>can not</r> write <b>comments</b> right now!"
                                )

                                return

                            except Exception:
                                logger.success(
                                    f"User <b>{self.username!r}</b> - <g>Successfully</g> posted comment {comment_count+1}/{count}: <b>{text!r}</b>"
                                )

                                # Increment comment count in report
                                Facebook.report[self.username]["comment"] += 1

                                break

                    time.sleep(1.5 + random.random())

                    if self.check_feature() is False:
                        return

            except Exception:
                logger.error(
                    f"User <b>{self.username!r}</b> - <r>Failed</r> to locate or interact with comment textbox."
                )
                if timeout > 0:
                    return self.comment(post_url, count, timeout - 1)

        else:
            logger.error("<r>No</r> comments available to post.")

    def like(self: Self, page_url: str, count: int) -> Union[bool, None]:
        self.driver.get(page_url)
        time.sleep(5)

        def like():
            like_buttons: List[WebElement] = self.driver.find_elements(
                By.XPATH, "//div[@aria-label='Like' and @role='button']"
            )

            for like_button in like_buttons:
                try:
                    self.scroll_into_view(like_button)
                    like_button.click()

                    logger.success(
                        f"User <b>{self.username}</b> - Like button successfully pressed. (Total Like: %s of {count})"
                        % (Facebook.report[self.username]["like"] + 1)
                    )

                    time.sleep(1 + random.random())

                except Exception:
                    logger.error(f"User <b>{self.username}</b> - An error occurred!")

                else:
                    Facebook.report[self.username]["like"] += 1

                    if Facebook.report[self.username]["like"] > count:
                        return True

        self.infinite_scroll(
            self.facebook_element, delay=2.5, scroll_limit=500, callback=like
        )

    def send_friend_request(self: Self, count: int = 100) -> None:
        self.driver.get("https://www.facebook.com/friends")
        time.sleep(5)

        def send_request():
            try:
                friends_element: WebElement = self.driver.find_element(
                    By.XPATH,
                    "//div[@aria-label='Friends' and @role='main']",
                )
                list_element: WebElement = friends_element.find_element(
                    By.XPATH,
                    "//div[@role='list']",
                )
                suggestions: List[WebElement] = list_element.find_elements(
                    By.XPATH,
                    "//div[@role='listitem']",
                )

                for suggestion in suggestions:
                    requests_count: int = Facebook.report[self.username][
                        "friend-requests"
                    ]

                    if requests_count >= count:
                        logger.success(
                            f"User <b>{self.username}</b> - The sending friend requests process completed!"
                        )

                        return True

                    try:
                        self.scroll_into_view(suggestion)

                        add_friend_button = suggestion.find_element(
                            By.XPATH,
                            "//div[@aria-label='Add friend' and @role='button']",
                        )
                        self.scroll_into_view(add_friend_button)
                        add_friend_button.click()
                        time.sleep(2.5)

                        try:
                            suggestion.find_element(
                                By.XPATH, "//span[contains(text(), 'Request sent')]"
                            )

                            Facebook.report[self.username]["friend-requests"] += 1

                            logger.success(
                                f"User <b>{self.username}</b> - Request <g>successfully</g> sent. [<c>{requests_count + 1}</c> of <c>{count}</c>]"
                            )

                        except Exception:
                            logger.warning(
                                f"User <b>{self.username}</b> - The request <y>was not</y> sent successfully."
                            )

                        if self.check_feature() is False:
                            return False

                    except Exception:
                        pass

            except Exception:
                logger.error(
                    f"User <b>{self.username}</b> - An error occurred during sending friend requests."
                )

        self.infinite_scroll(
            element=self.facebook_element,
            delay=2.5,
            callback=send_request,
        )

    def invite(self: Self, page_url: str, timeout: int = 5) -> None:
        self.driver.get(page_url)
        time.sleep(5)

        try:
            more_options_button: WebElement = self.driver.find_element(
                By.XPATH, "//div[@aria-label='See options' and @role='button']"
            )
            self.scroll_into_view(more_options_button)
            more_options_button.click()
            time.sleep(2.5)

            invite_friends_button: WebElement = self.driver.find_element(
                By.XPATH,
                "//span[contains(text(), 'Invite friends')]/ancestor::div[@role='menuitem']",
            )
            self.scroll_into_view(invite_friends_button)
            invite_friends_button.click()
            time.sleep(5)

            try:
                self.driver.find_element(
                    By.XPATH,
                    "//span[contains(text(), 'No Friends To Invite')]",
                )

                logger.warning(
                    f"User <b>{self.username}</b> - No <b>Friends</b> To Invite."
                )

                return
            except Exception:
                try:
                    select_all_button: WebElement = self.driver.find_element(
                        By.XPATH,
                        "//div[contains(@aria-label, 'Select All')][@role='button']",
                    )
                    select_all_button.click()
                    time.sleep(2.5)

                    send_invite_button: WebElement = self.driver.find_element(
                        By.XPATH,
                        "//div[@aria-label='Send Invites' and @role='button']",
                    )
                    send_invite_button.click()

                    for number in range(10):
                        try:
                            self.driver.find_element(
                                By.XPATH, "//span[contains(text(), 'Invites sent')]"
                            )

                            logger.success(
                                f"User <b>{self.username}</b> - Invites <g>successfully</g> sent."
                            )

                            return

                        except Exception:
                            pass

                        time.sleep(0.512)

                    else:
                        logger.warning(
                            f"User <b>{self.username}</b> - Invites may have <y>failed</y> to send."
                        )

                except Exception:
                    logger.warning(
                        f"User <b>{self.username}</b> - The <b>'Select All'</b> button was not found!"
                    )

        except Exception:
            logger.error(
                f"User <b>{self.username}</b> - An error occurred while sending invites. Retrying (<c>{timeout}</c> remaining)."
            )

            if timeout > 0:
                return self.invite(page_url, timeout - 1)

    def get_selectors_prefix(
        self: Self,
        post_url: Union[str, None] = None,
        suffix: Union[None, str] = None,
    ) -> str:
        if post_url is not None:
            self.driver.get(post_url)
            time.sleep(5)

        try:
            self.driver.find_element(
                By.XPATH,
                "//div[@role='dialog']{suffix}".format(suffix=suffix if suffix else ""),
            )
            logger.info(f"User <b>{self.username}</b> - Dialog Found!")

            return "//div[@role='dialog']"
        except Exception:
            logger.warning(f"User <b>{self.username}</b> - Dialog Not Found!")

            return str()

    def start(
        self: Self,
        *,
        page_url: str,
        username: Union[None, str] = None,
        groups: Union[None, List[str]] = None,
        like_count: int = 50,
        comment_count: int = 50,
        share_count: int = 5,
        friend_request_count: int = 50,
        send_invites: bool = False,
        cancel_all_friend_requests: bool = False,
        telegram_id: Union[int, None] = None,
    ):
        if username and username != self.username:
            return

        if post_url := self.get_last_post_url(page_url):
            prefix: str = self.get_selectors_prefix(
                post_url,
                suffix="//span[contains(text(), 'Share')]/ancestor::*[@role='button']",
            )

            def func():
                share_button = self.driver.find_element(
                    By.XPATH,
                    f"{prefix}//span[contains(text(), 'Share')]/ancestor::*[@role='button']",
                )
                self.scroll_into_view(share_button)
                logger.success(
                    f"User <b>{self.username}</b> has scrolled to the information section."
                )
                time.sleep(2.5)

            screenshots: List[bytes] = []

            if before_screenshot := self.get_screenshot(post_url, func):
                before = edit_image(
                    before_screenshot,
                    text="Before",
                    font_path=FONARTO_XT_PATH,
                    size=128,
                    position=(50, 25),
                    text_color=(255, 0, 0),
                )

                screenshots.append(before)

            if share_count > 0 and groups:
                self.share(post_url, groups, share_count)

            if comment_count > 0:
                self.comment(post_url, comment_count)

            if like_count > 0:
                self.like(page_url, like_count)

            if send_invites:
                self.invite(page_url)

            if friend_request_count > 0:
                self.send_friend_request(friend_request_count)

            if cancel_all_friend_requests:
                pass

            like = Facebook.report[self.username]["like"]
            comment = Facebook.report[self.username]["comment"]
            share = Facebook.report[self.username]["share"]
            friend_requests = Facebook.report[self.username]["friend-requests"]
            canceled_friend_requests = Facebook.report[self.username][
                "canceled-friend-requests"
            ]

            if after_screenshot := self.get_screenshot(post_url, func):
                after = edit_image(
                    after_screenshot,
                    text="After",
                    font_path=FONARTO_XT_PATH,
                    size=128,
                    position=(50, 25),
                    text_color=(255, 0, 0),
                )

                screenshots.append(after)

            caption: str = "\n".join(
                [
                    "Before and After Sharing the Facebook Post in Groups and Commenting.",
                    f"Username: {self.username}",
                    f"Page URL: {page_url}",
                    f"Post URL: {post_url}",
                    f"Like: {like}",
                    f"Comment: {comment}",
                    f"Share: {share}",
                    f"Friend Requests: {friend_requests}",
                    f"Cancelled Friend Requests: {canceled_friend_requests}",
                ]
            )

            photos: List[InputMediaPhoto] = [
                InputMediaPhoto(photo, caption=caption if not index else None)
                for index, photo in enumerate(screenshots)
            ]

            asyncio.run(self.telegram_bot.send_photos(*photos, chat_id=telegram_id))

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

    def cancel_all_friend_requests(self: Self, timeout: int = 5) -> None:
        self.driver.get("https://www.facebook.com/friends/requests")
        time.sleep(5)

        try:
            view_sent_requests_element: WebElement = self.driver.find_element(
                By.XPATH,
                "//span[contains(text(), 'View sent requests')]/ancestor::*[@role='button']",
            )
            view_sent_requests_element.click()
            time.sleep(2.5)

            dialog_element: WebElement = self.driver.find_element(
                By.XPATH,
                "//div[@role='dialog' and @aria-label='Sent Requests']",
            )

            last_child_element: WebElement = dialog_element.find_element(
                By.XPATH, "//div[last()]"
            )

            def cancel():
                try:
                    cancel_buttons: List[WebElement] = self.driver.find_elements(
                        By.XPATH,
                        "//div[@aria-label='Cancel request' and @role='button']",
                    )

                    for cancel_button in cancel_buttons:
                        try:
                            self.scroll_into_view(cancel_button)
                            cancel_button.click()

                            logger.success(
                                f"User <b>{self.username}</b> - The request <g>successfully</g> canceled."
                            )

                            Facebook.report[self.username][
                                "canceled-friend-requests"
                            ] += 1
                        except Exception:
                            logger.error(
                                f"User <b>{self.username}</b> - An error occurred during cancelling the request."
                            )
                        else:
                            time.sleep(1 + random.random())

                except Exception:
                    logger.error(f"User <b>{self.username}</b> - An error occurred!")

            self.infinite_scroll(last_child_element, delay=5, callback=cancel)

        except Exception:
            if timeout > 0:
                logger.warning(f"User <b>{self.username}</b> - Retrying...")
                return self.cancel_all_friend_requests(timeout - 1)


def start(
    cookie_file: str,
    page_url: str,
    username: Union[None, str] = None,
    groups: Union[None, List[str]] = None,
    like_count: int = 50,
    comment_count: int = 50,
    share_count: int = 5,
    friend_request_count: int = 50,
    send_invites: bool = False,
    cancel_all_friend_requests: bool = False,
    timeout: int = 5,
    credentials: Union[Dict[Literal["username", "password"], str], None] = None,
    telegram_id: Union[int, None] = None,
    **kwarg,
) -> None:
    try:  # handle exceptions
        with Account(
            cookie_file=cookie_file, credentials=credentials, **kwarg
        ) as account:
            if account:
                account.start(
                    page_url=page_url,
                    username=username,
                    groups=groups,
                    like_count=like_count,
                    comment_count=comment_count,
                    share_count=share_count,
                    friend_request_count=friend_request_count,
                    send_invites=send_invites,
                    cancel_all_friend_requests=cancel_all_friend_requests,
                    telegram_id=telegram_id,
                )
    except ReadTimeoutError as err:
        logger.error(f"Read Timeout Out Error: <r>{err}</r>")

        if timeout > 0:
            logger.info(
                f"<y>Retrying...</y> <c>{timeout}</c> attempt(s) remaining to start the process with URL: <c>{page_url}</c>"
            )
            return start(
                cookie_file,
                page_url,
                username,
                groups,
                like_count,
                comment_count,
                share_count,
                friend_request_count,
                send_invites,
                cancel_all_friend_requests,
                timeout - 1,
            )
