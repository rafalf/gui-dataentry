import pandas as pd
import os
from selenium import webdriver
from contextlib import contextmanager
from sys import platform
from webactions import WebActions
import logging
import logging.config
import json
import time
import yaml

LOGGING_CONFIG = {
    'formatters': {
        'brief': {
            'format': '[%(asctime)s][%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'brief'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'brief',
            'filename': 'log.log',
            'maxBytes': 1024*1024,
            'backupCount': 3,
        },
    },
    'loggers': {
        'main': {
            'propagate': False,
            'handlers': ['console', 'file'],
            'level': 'INFO'
        }
    },
    'version': 1
}

INPUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input.csv")
OUT_PUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.csv")
YAML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def read_yaml():
    with open(YAML, 'r') as stream:
        return yaml.load(stream)


def read_input():
    df = pd.read_csv(INPUT_CSV)
    return df.id.tolist()


def set_status(id_key, status="processed"):
    df = pd.read_csv(OUT_PUT)
    print("[INFO] {} set status: {}".format(id_key, status))
    df.loc[df['id'] == id_key, 'status'] = status
    df.to_csv(OUT_PUT, index=False)


def set_completed(id_key, completed):
    df = pd.read_csv(OUT_PUT)
    print("[INFO] {} set completed: {}".format(id_key, completed))
    df.loc[df['id'] == id_key, 'completed'] = completed
    df.to_csv(OUT_PUT, index=False)


def set_failed_to_select(id_key, not_completed):
    df = pd.read_csv(OUT_PUT)
    print("[INFO] {} set not_completed: {}".format(id_key, not_completed))
    df.loc[df['id'] == id_key, 'failed_to_select'] = not_completed
    df.to_csv(OUT_PUT, index=False)


def append_idx_key(idx_key):
    existing_df = pd.read_csv(OUT_PUT)
    append_df = pd.DataFrame([[idx_key, "", "", ""]], columns=["id", "status", "completed", "failed_to_select"])
    result = pd.concat([existing_df, append_df], ignore_index=True)
    result.to_csv(OUT_PUT, index=False)


def get_logger():
    logging.config.dictConfig(LOGGING_CONFIG)
    log = logging.getLogger('main')
    log.setLevel(level=logging.getLevelName('INFO'))
    return log


@contextmanager
def get_driver():

    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_argument("--disable-extensions")
    chromeOptions.add_argument("--disable-infobars")
    if platform == 'darwin':
        driver = webdriver.Chrome(chrome_options=chromeOptions)
    elif platform == 'linux' or platform == 'linux2':
        driver = webdriver.Chrome(chrome_options=chromeOptions)
    else:  # windows
        driver = webdriver.Chrome(os.path.join(BASE_DIR, "chromedriver.exe"),
                                  chrome_options=chromeOptions)

    yield driver
    driver.quit()


def esc_select(driver, logger):

    actions = WebActions(driver, logger)
    for _ in range(5):
        actions.send_esc_key()
        if not actions.is_element_by_css(".selectize-input.dropdown-active", 1):
            break
        else:
            time.sleep(1)
    else:
        set_status("esc failed")


def open_product(driver, logger):

    actions = WebActions(driver, logger)

    actions.open_url(read_yaml().get("url"))
    actions.wait_for_element_not_present_by_css("#preloader")

    actions.click_by_css("[data-automation-id=\"left-sidebar-cms-button\"]")
    actions.wait_for_element_by_css("[data-automation-id=\"left-sidebar-cms-button\"].active")

    actions.click_by_xpath("//div[normalize-space(@class)='bem-Pane_Body_Inner']//span[contains(text(),'Products')]")
    actions.wait_for_element_by_xpath(
        "//div[normalize-space(@class)='bem-Pane_Head']//span[contains(text(),'Products')]")

    logger.info("product panel displays")


def run():

    ids = read_input()
    logger = get_logger()
    yaml = read_yaml()

    with get_driver() as driver:

        driver.get(yaml.get("url_login"))
        driver.maximize_window()

        logger.info("url: %s", yaml.get("url_login"))

        actions = WebActions(driver, logger)

        actions.send_by_css("[ng-model=\"user.username\"]", yaml.get("user"))
        actions.send_by_css("[ng-model=\"user.password\"]", yaml.get("password"))
        actions.click_by_css("[data-automation-id=\"login-button\"]")

        actions.wait_for_element_by_css(".dropdown-click", visible=True)

        logger.info("logged in: %s %s", yaml.get("user"), yaml.get("password"))

        open_product(driver, logger)

        for idx, id_key in enumerate(ids, 1):

            try:
                completed = ""
                failed_to_select = ""

                if yaml.get("process_items") < idx:
                    logger.info("completed %s items set in config: process_items", yaml.get("process_items"))
                    break

                append_idx_key(id_key)

                logger.info("processing: %s", id_key)

                actions.send_by_css("input.bem-TextInput", id_key)
                time.sleep(1)

                for _ in range(3):
                    found = actions.get_all_elements_by_css_no_error(".bem-Table_Row",  wait_time=5)
                    if len(found) == 1:
                        logger.info("ok: one matching row found")
                        break
                    else:
                        logger.info("matching rows found  (%s) => wait and retry", len(found))
                        time.sleep(1)
                else:
                    logger.info("failed matching rows ...")

                    if len(found) == 0:
                        logger.info("0 key found %s. not processed", id_key)
                        set_status(id_key, "0 items found")
                        open_product(driver, logger)
                        continue
                    elif not yaml.get("process_multiple"):
                        logger.info("incorrect items found %s. not processed", len(found))
                        set_status(id_key, "errored: items found: (%s)" % len(found))
                        continue

                name = actions.get_element_by_css(".bem-Table_Row .bem-Text").text
                logger.info("processing item in table with name: %s", name)

                actions.click_by_css(".bem-Table_Row")
                actions.wait_for_element_by_xpath("//button/span[contains(text(),'Save')]", visible=True)

                # read inputs
                all_required = actions.get_all_elements_by_css(".bem-TextInput-required")
                required = [item.get_attribute("value") for item in all_required]

                all_not_required = actions.get_all_elements_by_css(".bem-TextInput")
                not_required = [item.get_attribute("value") for item in all_not_required]

                logger.info("brand hardcode is: %s", required[2])

                collections = not_required[5].split("; ")
                types = not_required[6].split("; ")
                categories = not_required[7].split("; ")

                logger.info("collections: %s, type: %s, category: %s", collections, types, categories)

                select_collections = []
                for category in categories:
                    for collection in collections:
                        select_collections.append(category + " " + collection)

                logger.info("select collection built: %s" % select_collections)

                select_types = []
                for category in categories:
                    for t in types:
                        select_types.append(category + " " + t)

                logger.info("select types built: %s" % select_collections)

                actions.scroll_into_view(".bem-Pane_Section:nth-of-type(2)")

                for collection in select_collections:
                    all_selects = actions.get_all_elements_by_css(".selectize-input")

                    actions.click_if_clickable(all_selects[0])
                    actions.wait_for_element_by_css(".selectize-input.dropdown-active")

                    all_drop_down = actions.get_all_elements_by_css(".selectize-dropdown-content>div")
                    drops = [drop.text for drop in all_drop_down]

                    if collection in drops:
                        logger.info("found collection: |%s| in drop down: %s", collection, drops)

                        actions.click_by_xpath("//div[contains(@class, 'selectize-dropdown-content')]/div[text()='" + collection + "']")
                        actions.wait_for_element_by_xpath("//div[contains(@class, 'selectize-input')]/div[text()='" + collection + "']")
                        completed += collection
                        completed += ";"

                    else:
                        logger.info("not found collection: |%s| in drop down: %s", collection, drops)
                        failed_to_select += collection
                        failed_to_select += ";"

                esc_select(driver, logger)

                actions.wait_for_element_not_present_by_css(".selectize-input.dropdown-active")

                for t in select_types:

                    all_selects = actions.get_all_elements_by_css(".selectize-input")

                    actions.click_if_clickable(all_selects[1])
                    actions.wait_for_element_by_css(".selectize-input.dropdown-active")

                    all_drop_down = actions.get_all_elements_by_css(".selectize-dropdown-content>div")
                    drops = [drop.text for drop in all_drop_down]

                    if t in drops:
                        logger.info("found type: |%s| in drop down: %s", t, drops)

                        actions.click_by_xpath("//div[contains(@class, 'selectize-dropdown-content')]/div[text()='" + t + "']")
                        actions.wait_for_element_by_xpath("//div[contains(@class, 'selectize-input')]/div[text()='" + t + "']")
                        completed += t
                        completed += ";"

                    else:
                        logger.info("not found type: |%s| in drop down: %s", t, drops)
                        failed_to_select += t
                        failed_to_select += ";"

                # to test only (type)
                # all_selects = actions.get_all_elements_by_css(".selectize-input")
                # actions.click_if_clickable(all_selects[1])
                # actions.wait_for_element_by_css(".selectize-input.dropdown-active")
                # actions.click_by_xpath(
                #     "//div[contains(@class, 'selectize-dropdown-content')]/div[contains(text(),'Women Tops')]")
                # actions.wait_for_element_by_xpath(
                #     "//div[contains(@class, 'selectize-input')]/div[contains(text(),'Women Tops')]")

                esc_select(driver, logger)

                for categ in categories:

                    all_selects = actions.get_all_elements_by_css(".selectize-input")

                    actions.click_if_clickable(all_selects[2])
                    actions.wait_for_element_by_css(".selectize-input.dropdown-active")

                    all_drop_down = actions.get_all_elements_by_css(".selectize-dropdown-content>div")
                    drops = [drop.text for drop in all_drop_down]

                    if categ in drops:
                        logger.info("found category: |%s| in drop down: %s", categ, drops)

                        actions.click_by_xpath("//div[contains(@class, 'selectize-dropdown-content')]/div[text()='" + categ + "']")
                        actions.wait_for_element_by_xpath("//div[contains(@class, 'selectize-input')]/div[text()='" + categ + "']")
                        completed += categ
                        completed += ";"

                    else:
                        logger.info("not found category: |%s| in drop down: %s", categ, drops)
                        failed_to_select += categ
                        failed_to_select += ";"

                esc_select(driver, logger)

                if yaml.get("save"):
                    actions.click_by_xpath("//button/span[text()='Save ']")
                    actions.wait_for_element_not_present_by_css("//button/span[contains(text(),'Save')]")

                    logger.info("saved product id: %s", id_key)
                else:
                    actions.click_by_xpath("//button/span[text()='Cancel']")

                    actions.wait_for_element_by_css(".bem-ConfirmWrapper .bem-ConfirmWrapper_Modal")

                    actions.click_by_xpath("//button[text()='Discard Changes']")
                    actions.wait_for_element_not_present_by_css(".bem-ConfirmWrapper .bem-ConfirmWrapper_Modal")

                set_status(id_key, "processed")
                set_completed(id_key, completed)
                set_failed_to_select(id_key, failed_to_select)

            except Exception as err:
                logger.error("%s: error: %s", err.__class__.__name__, err)
                set_status(id_key, "errored: (%s)" % err.__class__.__name__)

                open_product(driver, logger)


if __name__ == "__main__":

    run()