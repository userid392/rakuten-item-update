import configparser
import json
import base64


class RmsConfig:
    def __init__(
        self,
        config_path="config.ini",
        shop_config_path="shopsettings.json"
    ):
        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding="utf-8")
        self.settings = json.load(open(shop_config_path, 'r', encoding="utf-8"))

        self.login_id = self.config.get('login', 'login_id')
        self.login_password = self.config.get('login', 'login_password')
        self.user_id = self.config.get('login', 'user_id')
        self.user_password = self.config.get('login', 'user_password')
        
        self.timeout = int(self.config.get('web', 'timeout'))
        self.shop_bid = self.config.get('web', 'shop_bid')

        self.login_url = self.config.get('endpoint', 'login_url')
        self.mainmenu_url = self.config.get('endpoint', 'mainmenu_url')
        self.item_setting_menu_url = self.config.get('endpoint', 'item_setting_menu_url')
        self.item_edit_url = self.config.get('endpoint', 'item_edit_url')
        self.item_register_url = self.config.get('endpoint', 'item_register_url')
        self.item_search = self.config.get('endpoint', 'item_search')

        self.licenseKey = self.config.get('api', 'licenseKey')
        self.serviceSecret = self.config.get('api', 'serviceSecret')

        if self.login_id == "none":
            raise ValueError("login_idが入力されていません。")
        if self.login_password == "none":
            raise ValueError("login_passwordが入力されていません。")
        if self.user_id == "none":
            raise ValueError("user_idが入力されていません。")
        if self.user_password == "none":
            raise ValueError("user_passwordが入力されていません。")
        if self.licenseKey == "none":
            raise ValueError("licenseKeyが入力されていません。")
        if self.serviceSecret == "none":
            raise ValueError("serviceSecretが入力されていません。")

        self.auth_token = {"Authorization": self._auth(self.licenseKey, self.serviceSecret)}

    def _auth(self, licenseKey, serviceSecret):
        auth_token = (serviceSecret + ":" + licenseKey).encode('utf-8')
        return "ESA " + base64.b64encode(auth_token).decode('utf-8')
