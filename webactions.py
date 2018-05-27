import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import os
import time
import json


class WebActions:

    def __init__(self, driver, logger=None):
        self.driver = driver
        self.logger = logger

    def open_url(self, url):
        self.driver.get(url)

    @property
    def window_title(self):
        return self.driver.title

    def browser_back(self):
        self.driver.back()

    def get_current_url(self):
        return self.driver.current_url

    def switch_to_iframe(self, id_frame):
        WebDriverWait(self.driver, 30).until(EC.frame_to_be_available_and_switch_to_it(id_frame))

    def send_esc_key(self):
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

    def get_element_by_css(self, selector_css, wait_time=30):

        try:
            return WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((
                By.CSS_SELECTOR, selector_css)), 'get_element_by_css: element timed out: %s' % selector_css)
        except Exception as e:
            self.logger.error("%s: error: %s", e.__class__.__name__, e)
            raise WebDriverException("get_element_by_css failed")

    def is_element_by_css(self, selector_css, time_out=30, visible=False, clickable=False):

        try:
            if not visible and not clickable:
                WebDriverWait(self.driver, time_out).until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, selector_css)), 'is_element_by_css (presence): element timed out: %s' % selector_css)
            elif visible:
                WebDriverWait(self.driver, time_out).until(EC.visibility_of_element_located((
                    By.CSS_SELECTOR, selector_css)), 'is_element_by_css (visibility): element timed out: %s' % selector_css)
            elif clickable:
                WebDriverWait(self.driver, time_out).until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR, selector_css)), 'is_element_by_css (clickable): element timed out: %s' % selector_css)

            return True
        except TimeoutException as e:
            return None

    def get_element_by_css_no_wait(self, selector_css, visible=False):

        try:
            el = self.driver.find_element_by_css_selector(selector_css)
            if visible and el.is_displayed():
                return el
            elif visible and not el.is_displayed():
                raise Exception
            elif not visible:
                return el
        except Exception:
            return None

    def get_element_concatenate(self, element, selector_css):

        for _ in range(3):
            try:
                return element.find_element_by_css_selector(selector_css)
            except Exception as err:
                self.logger.warning("%s on get_element_concatenate", err.__class__.__name__)
                time.sleep(5)

        self.logger.error("get_element_concatenate failed on selector: %s", selector_css)
        raise WebDriverException("get_element_concatenate failed")

    def is_element_concatenate(self, element, selector_css):

        try:
            return element.find_element_by_css_selector(selector_css)
        except Exception as err:
            return None

    def get_element_clickable_by_css(self, selector_css, wait_time=30):

        try:
            return WebDriverWait(self.driver, wait_time).until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, selector_css)), 'get_element_clickable_by_css: element timed out: %s' % selector_css)
        except Exception as e:
            self.logger.error("%s: error: %s", e.__class__.__name__, e)
            raise WebDriverException("get_element_clickable_by_css failed")

    def click_by_css(self, selector_css, scroll_into=False):

        for _ in range(3):
            try:
                el = self.get_element_clickable_by_css(selector_css)
                if scroll_into:
                    el.location_once_scrolled_into_view
                el.click()
                return
            except Exception as err:
                self.logger.warning("(%s) failed to click: %s ", err.__class__.__name__, err)
                time.sleep(1)
        else:
            self.logger.error("failed to click")
            raise WebDriverException("click_by_css failed")

    def scroll_into_view(self, selector):

        el = self.get_element_by_css(selector)
        el.location_once_scrolled_into_view

    def click_if_clickable(self, element):

        for _ in range(3):
            try:
                if element.is_enabled() and element.is_displayed():
                    element.click()
                    return
                else:
                    self.logger.info('click_if_clickable not yet')
                    time.sleep(1)
            except Exception as err:
                self.logger.warning("(%s) click_if_clickable failed to click", err.__class__.__name__)
                time.sleep(1)
        else:
            self.logger.error("failed to click")
            raise WebDriverException("click_if_clickable failed")

    def click_by_xpath(self, xpath):

        for _ in range(3):
            try:
                self.get_element_clickable_by_xpath(xpath).click()
                return
            except Exception as err:
                self.logger.warning("(%s) failed to click on: %s", err.__class__.__name__, xpath)
                time.sleep(1)
        else:
            self.logger.error("failed to click")
            raise WebDriverException("click_by_xpath failed")

    def send_by_css(self, selector_css, value):

        for _ in range(3):
            try:
                el = self.get_element_by_css(selector_css)
                el.clear()
                el.send_keys(value)
                return
            except Exception as err:
                self.logger.warning("(%s) failed on: %s", err.__class__.__name__, selector_css)
                time.sleep(1)
        else:
            self.logger.error("failed to send")
            raise WebDriverException("send_by_css failed")

    def get_element_by_xpath(self, selector_xpath, wait_time=30):

        try:
            return WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((
                By.XPATH, selector_xpath)), 'get_element_by_xpath: element timed out: %s' % selector_xpath)
        except Exception as e:
            self.logger.error("%s: error: %s", e.__class__.__name__, e)
            raise WebDriverException("get_element_by_xpath failed")

    def get_element_clickable_by_xpath(self, selector_xpath, wait_time=30):

        try:
            return WebDriverWait(self.driver, wait_time).until(EC.element_to_be_clickable((
                By.XPATH, selector_xpath)), 'get_element_clickable_by_xpath: element timed out: %s' % selector_xpath)
        except Exception as e:
            self.logger.error("%s: error: %s", e.__class__.__name__, e)
            raise WebDriverException("get_element_clickable_by_xpath failed")

    def get_all_elements_by_css(self, selector_css, wait_time=30):

        try:
            return WebDriverWait(self.driver, wait_time).until(EC.presence_of_all_elements_located((
                By.CSS_SELECTOR, selector_css)), 'get_all_elements_by_css: element timed out: %s' % selector_css)
        except Exception as e:
            self.logger.error("%s: error: %s", e.__class__.__name__, e)
            raise WebDriverException("get_all_elements_by_css failed")

    def get_all_elements_by_css_no_wait(self, selector):
        return self.driver.find_elements_by_css_selector(selector)

    def get_all_elements_by_css_no_error(self, selector_css, wait_time=30):

        try:
            return WebDriverWait(self.driver, wait_time).until(EC.presence_of_all_elements_located((
                By.CSS_SELECTOR, selector_css)), 'get_all_elements_by_css_no_error: element timed out: %s' % selector_css)
        except Exception as e:
            self.logger.info("%s", e.__class__.__name__)
            return []

    def get_element_by_link_text(self, text, wait_time=30):

        try:
            return WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((
                By.LINK_TEXT, text)), 'get_element_by_link_text: element timed out: %s' % text)
        except Exception as e:
            self.logger.error("%s: error: %s", e.__class__.__name__, e)
            raise WebDriverException("get_element_by_link_text failed")

    def get_element_visible_by_css_no_wait(self, selector_css):

        try:
            el = self.driver.find_element_by_css_selector(selector_css)
            if el.is_displayed():
                return el
            raise WebDriverException("get_element_visible_by_css_no_wait failed")
        except:
            return None

    def wait_for_element_by_css(self, selector_css, wait_time=30, visible=False, fail=True):

        try:
            if visible:
                WebDriverWait(self.driver, wait_time).until\
                    (EC.visibility_of_element_located((By.CSS_SELECTOR, selector_css)),
                        'wait_for_element_by_css: element timed out: %s' % selector_css)
            else:
                WebDriverWait(self.driver, wait_time).\
                    until(EC.presence_of_element_located((By.CSS_SELECTOR, selector_css)),
                        'wait_for_element_by_css: element timed out: %s' % selector_css)
            return True
        except Exception as e:
            if fail:
                self.logger.error("%s: error: %s", e.__class__.__name__, e)
                raise WebDriverException("wait_for_element_by_css failed")
            else:
                return None

    def wait_for_element_not_present_by_css(self, selector_css, wait_time=60, visible=False):

        try:
            if visible:
                WebDriverWait(self.driver, wait_time).until_not\
                        (EC.visibility_of_element_located((By.CSS_SELECTOR, selector_css)),
                         '(not) visibility_of_element_located: element timed out: %s' % selector_css)
            else:
                WebDriverWait(self.driver, wait_time).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector_css)),
                    '(not) presence_of_element_located: element timed out: %s' % selector_css)
        except Exception as e:
            self.logger.error("%s: error: %s", e.__class__.__name__, e)
            raise WebDriverException("wait_for_element_not_present_by_css failed")

    def wait_until_element_not_visible_by_css(self, selector_css, wait_time=30):

        try:
            WebDriverWait(self.driver, wait_time).until_not(EC.visibility_of_element_located((
                By.CSS_SELECTOR, selector_css)),
                'wait_until_element_not_visible_by_css: element timed out: %s' % selector_css)
        except Exception as e:
            self.logger.error("%s: error: %s", e.__class__.__name__, e)
            raise WebDriverException("wait_until_element_not_visible_by_css failed")

    def wait_for_element_by_xpath(self, selector_xpath, wait_time=30, visible=False):

        try:
            if visible:
                WebDriverWait(self.driver, wait_time).until(EC.visibility_of_element_located((
                    By.XPATH, selector_xpath)), 'wait_for_element_by_xpath: element timed out: %s' % selector_xpath)
            else:
                WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((
                    By.XPATH, selector_xpath)), 'wait_for_element_by_xpath: element timed out: %s' % selector_xpath)
        except Exception as e:
            self.logger.error("%s: error: %s", e.__class__.__name__, e)
            raise WebDriverException("wait_for_element_by_xpath failed")

    def wait_until_element_not_present_by_css(self, selector_css, wait_time=10):

        try:
            WebDriverWait(self.driver, wait_time).until_not(EC.presence_of_element_located((
                By.CSS_SELECTOR, selector_css)), 'element timed out: %s' % selector_css)
        except Exception as e:
            self.logger.error("%s: error: %s", e.__class__.__name__, e)
            raise WebDriverException("wait_until_element_not_present_by_css failed")

    def wait_until_element_settles(self, selector, by="css selector"):

        try:
            store_location = {}
            for _ in range(30):
                el = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((
                    by, selector)), 'wait_until_element_settles: element timed out: %s' % selector)
                current_location = el.location
                if store_location == current_location:
                    break
                else:
                    time.sleep(1)
                    store_location = current_location
        except Exception as e:
            self.logger.error("%s: error: %s", e.__class__.__name__, e)
            raise WebDriverException("wait_until_element_settles failed")

    def wait_for_alert(self):

        WebDriverWait(self.driver, 60).until(EC.alert_is_present())

    def accept_alert_if_present(self):
        try:
            alert = self.driver.switch_to_alert()
            alert.accept()
        except:
            pass

    def is_alert_present(self):
        if EC.alert_is_present:
            return True

