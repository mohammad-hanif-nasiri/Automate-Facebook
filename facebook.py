import os
import pickle
import random
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Self, Union

import click
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager

from console import console
from functions import send_email, get_comments
from logger import logger
from exceptions import ShareLimitException


class Facebook:

    report: Dict[str, Dict[str, Any]] = {}
    driver_path: str = ChromeDriverManager().install()

    @staticmethod
    def save_cookies(driver: webdriver.Chrome) -> None:
        """
        Static method to save cookies from the current browser session after a successful login.

        Parameters:
        -----------
        driver : webdriver.Chrome
            The Selenium Chrome WebDriver instance from which cookies will be saved.

        Returns:
        --------
        None :
            Saves the cookies to a `.pkl` file in the 'pkl' directory with a unique filename.
        """
        # Save cookies after successful login
        pickle.dump(
            driver.get_cookies(),
            open(f"pkl/{uuid.uuid4()}.pkl", "wb"),
        )

    @staticmethod
    def load_cookies(driver: webdriver.Chrome, cookie_file: str) -> None:
        """
        Load cookies from a specified .pkl file into the Selenium WebDriver.

        Parameters:
        -----------
        driver : webdriver.Chrome
            The Selenium Chrome WebDriver instance into which cookies will be loaded.
        cookie_file : str
            The path to the .pkl file containing the cookies to be loaded.

        Returns:
        --------
        None
        """
        # Info: Starting cookie management process
        logger.info(
            "Starting the process to load and add cookies (file: {cookie_file})."
        )

        # Remove all current cookies
        driver.delete_all_cookies()
        logger.info("All existing cookies have been deleted from the driver.")

        # Load cookies from the .pkl file
        with open(cookie_file, "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)

        # Success: Cookies have been loaded and added
        logger.success(
            "Cookies have been <g>successfully</g> loaded from the file and added to the driver."
        )

    @staticmethod
    def login(
        driver: webdriver.Chrome,
        username: Union[None, str] = None,
        password: Union[None, str] = None,
    ) -> bool:
        """
        Static method to log into a Facebook account using Selenium WebDriver.

        Parameters:
        -----------
        driver : webdriver.Chrome
            The Selenium Chrome WebDriver instance used to interact with the Facebook login page.
        username : Union[None, str], optional
            The username or email associated with the Facebook account. Default is None.
        password : Union[None, str], optional
            The password for the Facebook account. Default is None.

        Returns:
        --------
        bool :
            Returns True if login is successful, otherwise returns False.
        """
        # Open Facebook login page
        driver.get("https://www.facebook.com/login")

        if username and password:
            try:
                # Locate email, password fields, and login button
                email_field = driver.find_element(By.ID, "email")
                password_field = driver.find_element(By.ID, "pass")
                login_button = driver.find_element(By.NAME, "login")

                # Enter login credentials
                email_field.send_keys(username)
                password_field.send_keys(password)

                # Submit login form
                login_button.click()

                # Wait for page to load and check if login was successful
                time.sleep(
                    3
                )  # You can also use WebDriverWait for a more robust solution

                # Check if there is an element that indicates successful login, e.g., Facebook home button
                try:
                    driver.find_element(
                        By.XPATH, "//*[contains(@href, 'https://www.facebook.com/')]"
                    )

                    logger.success(
                        f"Login <b><g>successful</g></b> for user: <b>{username!r}</b>"
                    )

                    console.input(
                        "Press Enter to continue and save cookies as a .pkl file."
                    )

                    Facebook.save_cookies(driver)

                    return True  # Login was successful
                except NoSuchElementException:
                    logger.error(
                        f"Login <r><b>failed</b></r> for user: <b>{username!r}</b>"
                    )
                    return False  # Login failed (possibly due to wrong credentials)
            except (NoSuchElementException, TimeoutException) as _:
                # Handle case where login page elements couldn't be found
                return False
        else:
            # If no username and password are provided, prompt for manual login
            logger.info("Please perform manual login in the browser.")

            console.input(
                "Press Enter to continue after you have manually logged in..."
            )

            # Check if login was successful after manual intervention
            try:
                driver.find_element(
                    By.XPATH, "//*[contains(@href, 'https://www.facebook.com/')]"
                )

                logger.success(
                    f"Login <b><g>successful</g></b> for user: <b>{username!r}</b>"
                )

                console.input(
                    "Press Enter to continue and save cookies as a .pkl file."
                )

                Facebook.save_cookies(driver)

                return True  # Manual login was successful
            except NoSuchElementException:
                logger.error(
                    f"Login <r><b>failed</b></r> for user: <b>{username!r}</b>"
                )

                return False  # Manual login failed or not completed


class Account(Facebook):
    def __init__(self: Self, cookie_file: str, *args, **kwargs) -> None:
        """
        Initializes the Facebook automation bot with specified options and cookies.

        This constructor sets up a Chrome WebDriver instance with various options for headless
        operation, GPU acceleration, and notifications. It also loads a specified cookie file
        for user authentication.

        Parameters:
        -----------
        cookie_file : str
            Path to the file containing cookies to be loaded into the WebDriver session.

        *args
            Additional positional arguments for extended functionality.

        **kwargs
            Keyword arguments for enabling/disabling WebDriver options:
            - headless (bool): Enables headless mode if True.
            - disable_gpu (bool): Disables GPU acceleration if True.
            - disable_infobars (bool): Disables infobars if True.
            - disable_extensions (bool): Disables browser extensions if True.
            - start_maximized (bool): Starts browser maximized if True.
            - no_sandbox (bool): Disables sandbox mode if True.
            - block_notifications (bool): Blocks browser notifications if True.

        Returns:
        --------
        None
        """
        self.options: Options = Options()

        if kwargs.get("headless", False):
            self.options.add_argument("--headless")

        if kwargs.get("disable_gpu", False):
            self.options.add_argument("--disable-gpu")

        if kwargs.get("disable_infobars", False):
            self.options.add_argument("--disable-infobars")

        if kwargs.get("disable_extensions", False):
            self.options.add_argument("--disable-extensions")

        if kwargs.get("start_maximized", False):
            self.options.add_argument("start-maximized")

        if kwargs.get("no_sandbox", False):
            self.options.add_argument("--no-sandbox")

        if kwargs.get("block_notifications", False):
            self.options.add_experimental_option(
                "prefs",
                {
                    "profile.default_content_setting_values.notifications": 1,
                },
            )

        self.service: Service = Service(self.driver_path)

        self.driver: webdriver.Chrome = webdriver.Chrome(
            service=self.service,
            options=self.options,
        )

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
        X = element.location.get("x")
        Y = element.location.get("y")

        self.driver.execute_script(
            f"window.scrollTo({X}, {Y}); ",
            element,
        )

        for _ in range(10):
            self.facebook_element.send_keys(Keys.UP)

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

        if self.driver.current_url != (url := "https://facebook.com"):
            self.driver.get(url)
            time.sleep(5)

        try:
            link = self.driver.find_element(
                By.XPATH, '//div[@aria-label="Shortcuts"]//a'
            )
            if href := link.get_attribute("href"):
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

    def like(self: Self, page_url: str, count: int = 50) -> Union[bool, None]:
        """
        Likes a specified number of posts on a given Facebook page.

        This method locates the "Like" buttons on the specified Facebook page and clicks
        on them to like the posts. It continues to like posts until either the specified
        count is reached or there are no more like buttons available.

        Parameters:
        -----------
        page_url: str
            The URL of the Facebook page containing the posts to like. This should be
            a valid URL that the user has access to.

        count: int
            The number of posts to like. The method will attempt to like this many posts
            on the specified page. If there are fewer available posts, it will like as many
            as possible.

        Returns:
        --------
        Union[bool, None]
            Returns True if the specified number of likes is successfully performed,
            or None if the action could not be completed due to an error.

        Raises:
        -------
        WebDriverException
            If there is an issue with the WebDriver while trying to interact with the
            page elements.

        Example:
        ---------
        >>> like_success = like(page_url="https://www.facebook.com/yourpage", count=5)
        >>> if like_success:
        >>>     print("Successfully liked the posts.")
        """
        if self.driver.current_url != page_url:
            self.driver.get(page_url)
            time.sleep(5)

        try:
            like_buttons: List[WebElement] = [
                button
                for button in self.driver.find_elements(
                    By.XPATH,
                    "//div[@aria-label='Like']//span[contains(@class, 'x3nfvp2')]//i/ancestor::div[@role='button']",
                )
            ]

            for like_button in like_buttons:
                try:
                    self.scroll_into_view(element=like_button)

                    like_button.click()
                    time.sleep(2.5)

                    logger.success(
                        f"User <b>{self.username!r}</b> - <g>Successfully</g> post liked."
                    )

                    if Facebook.report[f"{self.username}"]["like"] >= count:
                        logger.info(
                            f"<b>Completed</b> the like operation for user: <b>{self.username!r}</b>."
                        )
                        return True

                    # Increment like count in report
                    Facebook.report[f"{self.username}"]["like"] += 1

                except Exception as _:
                    logger.error(
                        f"User <b>{self.username!r}</b> - <r>Error</r> clicking like button."
                    )

        except Exception as _:
            logger.error(
                f"User {self.username!r} - <r>Failed</r> to like posts on {page_url!r}."
            )

    def comment(self: Self, page_url: str, count: int = 50) -> Union[None, bool]:
        """
        Posts comments on a specified number of posts on a Facebook page.

        This method navigates to the provided Facebook page URL, locates comment buttons on posts,
        and posts a random comment from a pre-defined list. It will continue to post comments until
        reaching the specified count limit or encountering an error.

        Parameters:
        -----------
        page_url: str
            The URL of the Facebook page where comments will be posted.

        count: int
            The maximum number of comments to post. If the count is reached, the method stops.

        Returns:
        --------
        bool
            True if the comment process completed up to the specified count.
            Returns None if an error occurs during the comment process.

        Raises:
        -------
        WebDriverException
            If there is an issue with the Selenium WebDriver while navigating, locating elements,
            or interacting with the page.
        """

        if self.driver.current_url != page_url:
            logger.info(f"Navigating to the Facebook page: {page_url}")
            self.driver.get(page_url)
            time.sleep(5)

        # Retrieve comments and prepare to post
        if comments := get_comments():
            self.facebook_element.send_keys(Keys.ESCAPE)
            try:
                comment_textbox_elements: List[WebElement] = self.driver.find_elements(
                    By.XPATH,
                    '//div[@aria-label="Write a comment…"]',
                )

                for comment_textbox in comment_textbox_elements:
                    try:
                        self.scroll_into_view(element=comment_textbox)

                        for i in range(int(count / 100 * 50)):
                            comment_textbox.send_keys(Keys.ESCAPE)
                            comment_textbox.send_keys(text := random.choice(comments))
                            comment_textbox.send_keys(Keys.ENTER)
                            time.sleep(2.5)

                            logger.success(
                                f"User <b>{self.username!r}</b> - <g>Successfully</g> posted comment {i+1}/{count}: <b>{text!r}</b>"
                            )

                            if Facebook.report[f"{self.username}"]["comment"] >= count:
                                logger.info(
                                    f"User <b>{self.username!r}</b> - <b>Completed</b> commenting on <b>{int(count / 100 * 50)}</b> posts for user."
                                )
                                return True

                            # Increment comment count in report
                            Facebook.report[f"{self.username}"]["comment"] += 1

                            try:
                                dialog_element = self.driver.find_element(
                                    By.XPATH, "//div[role='dialog']"
                                )
                                heading_element = dialog_element.find_element(
                                    By.XPATH, "//h2[dir='auto']"
                                )

                                logger.warning(
                                    f"<yellow><b>{heading_element.text}</b></yellow>"
                                )

                                self.facebook_element.send_keys(Keys.ESCAPE)

                                return False
                            except Exception as _:
                                pass

                    except Exception as _:
                        logger.error(
                            "User <b>{self.username!r}</b> - <r>Failed</r> to post a comment."
                        )

            except Exception as _:
                logger.error(
                    "User <b>{self.username!r}</b> - <r>Failed</r> to locate or interact with comment buttons."
                )

        else:
            logger.error("<r>No</r> comments available to post.")

    def share(self: Self, page_url: str, group: str, timeout: int = 5) -> bool:
        if self.driver.current_url != page_url:
            self.driver.get(page_url)
            self.infinite_scroll(scroll_limit=5, delay=2.5)
            time.sleep(5)

        try:
            # Find the first "Share" button on the page
            share_button = self.driver.find_element(
                By.XPATH,
                "//span[contains(text(), 'Share')]/ancestor::*[@role='button']",
            )
            self.scroll_into_view(share_button)

            share_button.click()
            time.sleep(2.5)

            # Select the "Share to a Group" option
            share_to_group_button = self.driver.find_element(
                By.XPATH,
                "//span[contains(text(), 'Group')]/ancestor::*[@role='button']",
            )
            share_to_group_button.click()
            time.sleep(2.5)

            search_input = self.driver.find_element(
                By.XPATH, '//input[@placeholder="Search for groups"]'
            )
            search_input.send_keys(group)
            time.sleep(2.5)

            group_elem = self.driver.find_element(
                By.XPATH,
                f"//span[contains(text(), '{group}')]/ancestor::*[@role='button']",
            )
            group_elem.click()
            time.sleep(2.5)

            post_button = self.driver.find_element(
                By.XPATH, "//div[@aria-label='Post']"
            )
            post_button.click()

            for _ in range(10):
                try:
                    self.driver.find_element(
                        By.XPATH, "//span[contains(text(), 'Shared to your group.')]"
                    )
                    logger.success(
                        f"User <b>{self.username!r}</b> - The post was <b><g>successfully</g></b> shared in the group <b>{group!r}</b>."
                    )

                    return True
                except Exception as _:
                    pass

                time.sleep(1)

        except Exception as _:
            if timeout > 0:
                logger.info(
                    f"User {self.username!r} - Attempting to share the post to group {group!r}. "
                    f"Retries remaining: {timeout}."
                )

                self.driver.refresh()
                self.infinite_scroll(scroll_limit=5, delay=2.5)

                return self.share(page_url, group, timeout - 1)

        logger.error(
            f"User <b>{self.username!r}</b> - <r>Unable</r> to share the post."
        )

        return False

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
        if username and username != self.username:
            return

        self.driver.get(page_url)
        time.sleep(10)

        self.infinite_scroll(scroll_limit=2)

        if groups:
            finished: bool = False
            for group in groups:
                for index in range(share_count):
                    try:
                        logger.info(
                            f"Preparing to share the latest post... (Attempt <c>{index}</c> of <c>{share_count}</c>)"
                        )
                        if self.share(page_url, group):
                            # Increment share count in report
                            Facebook.report[f"{self.username}"]["share"] += 1
                    except ShareLimitException as error:
                        logger.error(f"<r>{error}</r>")

                        finished = True
                        break

                if finished:
                    break

        if like_count > 0:
            self.infinite_scroll(
                delay=2.5,
                scroll_limit=500,
                callback=self.like,
                page_url=page_url,
                count=like_count,
            )

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
                    return

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
    *args,
    **kwarg,
):
    with Account(cookie_file, *args, **kwarg) as account:
        if account:
            account.start(
                page_url=page_url,
                username=username,
                groups=groups,
                like_count=like_count,
                comment_count=comment_count,
                share_count=share_count,
            )


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
def cli(
    headless: bool,
    disable_gpu: bool,
    disable_infobars: bool,
    disable_extensions: bool,
    start_maximized: bool,
    block_notifications: bool,
    no_sandbox: bool,
):
    # Log the values of each parameter
    logger.info(f"Headless mode: {headless}")
    logger.info(f"Disable GPU: {disable_gpu}")
    logger.info(f"Disable infobars: {disable_infobars}")
    logger.info(f"Disable extensions: {disable_extensions}")
    logger.info(f"Start maximized: {start_maximized}")
    logger.info(f"Block notifications: {block_notifications}")
    logger.info(f"Sandbox: {no_sandbox}")


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
    """
    Main command  for interacting with Facebook posts and groups.

    This command provides options to like posts, comment on posts,
    and share posts within specified groups on Facebook. Users can
    specify their username, the page URL for the posts, and group
    names for sharing.
    """

    threads: List[threading.Thread] = []

    if os.path.exists("pkl/"):
        for pkl in os.listdir("pkl"):
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

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    if Facebook.report:
        cols: List[str] = ["#", "Username", "Like", "Comment", "Share"]
        rows: List[List[Any]] = []

        for index, (username, data) in enumerate(Facebook.report.items()):
            like = data.get("like")
            comment = data.get("comment")
            share = data.get("share")

            row = [index + 1, username, like, comment, share]
            rows.append(row)

        send_email("Automate - Facebook", cols=cols, rows=rows)


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
    Log into a Facebook account using Selenium WebDriver.

    This command opens a Chrome browser, navigates to the Facebook login page,
    and attempts to log in using the provided username and password. The browser
    can be configured with several options to customize its behavior during
    the session.
    """
    options: Options = Options()

    if ctx.params.get("headless", False):
        options.add_argument("--headless")

    if ctx.params.get("disable_gpu", False):
        options.add_argument("--disable-gpu")

    if ctx.params.get("disable_infobars", False):
        options.add_argument("--disable-infobars")

    if ctx.params.get("disable_extensions", False):
        options.add_argument("--disable-extensions")

    if ctx.params.get("start_maximized", False):
        options.add_argument("start-maximized")

    if ctx.params.get("block_notifications", False):
        options.add_experimental_option(
            "prefs",
            {
                "profile.default_content_setting_values.notifications": 1,
            },
        )

    service: Service = Service(
        ChromeDriverManager().install(),
    )

    driver: webdriver.Chrome = webdriver.Chrome(
        service=service,
        options=options,
    )

    Facebook.login(driver, username=username, password=password)


if __name__ == "__main__":
    cli()
