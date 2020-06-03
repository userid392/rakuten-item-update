from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By


from datamanager import RmsConfig

import time
import requests
import xml.etree.ElementTree as ET
import math


class RakutenRms:
    def __init__(self):
        self.config = RmsConfig()

        for k, v in self.config.settings.items():
            self.config.settings[k]["toggle"] = False
        
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        # options.add_argument("--disable-gpu")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-desktop-notifications")
        options.add_argument("--disable-extensions")
        self.driver = webdriver.Chrome(
            "chromedriver.exe",
            options=options)

        self.timeout = self.config.timeout

    def chunk_search(
            self,
            searchkey,
            offset="0",
            limit="30",
            sortKey="itemRegTime",
            sortOrder="desc"):
        
        params = {
            "offset": offset,
            "limit": limit,
            "sortKey": sortKey,
            "sortOrder": sortOrder,
        }
        params.update(searchkey)

        params = {k: str(v) for k, v in params.items()}

        response = requests.get(
            self.config.item_search,
            headers=self.config.auth_token,
            params=params)

        response.raise_for_status()

        result_xml = ET.fromstring(response.text)[1]
        if int(result_xml[1].text) > 0 and len(result_xml) > 2:
            items = result_xml[2]
        else:
            items = []

        time.sleep(1)
        return items, int(result_xml[1].text)

    def search(self,
               searchkey,
               offset="0",
               limit="50",
               sortKey="itemRegTime",
               sortOrder="desc"):
        current_offset = int(offset)
        items, item_num = self.chunk_search(
            searchkey, str(current_offset), limit, sortKey, sortOrder)
        yield items, item_num

        current_offset += int(limit)

        num_chunks = math.ceil(item_num / int(limit))
        for i in range(num_chunks):
            items, item_num = self.chunk_search(
                searchkey, str(current_offset), limit, sortKey, sortOrder)
            current_offset += int(limit)
            yield items, item_num

    def nextsearch(self,
                   items,
                   searchkey):

        new_items = []
        for item in items:
            for k, v in searchkey.items():
                if v not in item.find(k).text:
                    break
            else:
                new_items.append(item)

        return new_items

    def login(self):
        # ログインページにアクセス
        self.driver.get(self.config.login_url)

        # ログインフォームが表示されるまで待機
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//form[@action=\"{}\"]".format(self.config.login_url))
                )
            )
        except TimeoutException as te:
            print(te.message)

        # R-Login ID
        self.driver.find_element_by_name(
            "login_id").send_keys(self.config.login_id)

        # R-Login パスワード
        self.driver.find_element_by_name(
            "passwd").send_keys(self.config.login_password)

        self.driver.find_element_by_name("submit").click()

        # ログインフォームが表示されるまで待機
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//form[@action=\"{}\"]".format(self.config.login_url))
                )
            )
        except TimeoutException as te:
            print(te.message)

        # ユーザID
        self.driver.find_element_by_name(
            "user_id").send_keys(self.config.user_id)

        # パスワード
        self.driver.find_element_by_name(
            "user_passwd").send_keys(self.config.user_password)

        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//form[@action=\"{}\"]".format(self.config.login_url))
                )
            )
            self.driver.find_element_by_name("submit").click()

        except TimeoutException as te:
            print(te.message)

        WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//form[@action=\"{}\"]".format(self.config.login_url))
            )
        )
        self.driver.find_element_by_name("submit").click()

        WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//form[@action=\"{}\"]".format(self.config.mainmenu_url))
            )
        )
        self.driver.find_element_by_xpath(
            "//button[@type=\"submit\"]").click()

    def updateShopsettings(self):
        self.driver.get(self.config.item_setting_menu_url)

        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_all_elements_located)
        except TimeoutException as te:
            print(te.message)

        elements = self.driver.find_elements_by_tag_name("a")
        for el in elements:
            if el.get_attribute("href").find(self.config.item_register_url) != -1:
                el.click()
                break

        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_all_elements_located)
        except TimeoutException as te:
            print(te.message)

        for k, tag in self.config.settings.items():
            if tag['type'] == 'select':
                select_element = self.driver.find_element_by_name(
                    tag['attr_name'])
                option_elements = select_element.find_elements_by_tag_name('option')
                options = {el.get_attribute('value'): el.text.strip() for el in option_elements}
                
                self.config.settings[k]['options'] = options
            
        if self.config.shop_bid == "auto":
            self.config.shop_bid = self.driver.find_element_by_name("shop_bid").get_attribute("value")
    
    def select(self, name: str, select_number: str):
        element = self.driver.find_element_by_name(name)
        select_element = Select(element)
        select_element.select_by_value(select_number)

    def checkbox(self, name: str, check: bool):
        element = self.driver.find_element_by_name(name)
        print(check, element.is_selected())
        if element.is_selected() != check:
            element.click()

    def radio(self, name: str, value: str):
        elements = self.driver.find_elements_by_name(name)
        for element in elements:
            if element.get_attribute("value") == str(value):
                element.click()
                break

    def textarea(self, name: str, insert=("", ""), replace=("", "")):
        element = self.driver.find_element_by_name(name)
        element.clear()
        text = element.text
        text = text.replace(replace[0], replace[1])

        before, after = insert
        element.send_keys(before + text + after)

    def update(self, mng_number):
        self.driver.get(self.config.item_edit_url + "&shop_bid=" + self.config.shop_bid + "&mng_number=" + mng_number)
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_all_elements_located)
        except TimeoutException as te:
            print(te.message)

        for k, item in self.config.settings.items():
            if not item['toggle']:
                continue
            tag_type = item['type']

            if tag_type == "select":
                self.select(item['attr_name'], item['value'])
            elif tag_type == "checkbox":
                self.checkbox(item['attr_name'], item['value'])
            elif tag_type == "radio":
                self.radio(item['attr_name'], item['value'])
            elif tag_type == "text":
                self.textarea(
                    item['attr_name'],
                    item['insert'],
                    item['replace'])

        time.sleep(0.5)
        self.driver.find_element_by_id("submitButton").click()
