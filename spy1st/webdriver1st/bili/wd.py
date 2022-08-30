import random

import requests
from retrying import retry, RetryError
from seleniumwire import webdriver

# USER_DATA_DIR = r"C:\Users\Administrator\.chrome_user_data"
USER_DATA_DIR = r"/Users/hh/Library/Application Support/Google/Chrome"
EXECUTABLE_PATH = r"/Users/hh/Documents/tools_using/chromedriver"
IP_BLACKLIST_FILE = r'C:\Users\Administrator\.ip_blacklist.txt'


class RobotWebdriver:
    """
    用于机器人的WebDriver
    """

    def __init__(self, use_proxy=False, headless=False, exe_path=None, proxy_session=0):
        self._use_proxy = use_proxy
        self._proxy_session = proxy_session
        self._headless = headless
        self._exe_path = exe_path

    @classmethod
    def create(cls, use_proxy=False, headless=False, exe_path=None, proxy_session=0):
        return cls(use_proxy, headless, exe_path, proxy_session)._create0()

    @classmethod
    def create_local(cls, exe_path=None):
        return cls().create(exe_path=exe_path)

    def _create0(self):
        # https://support.mozilla.org/en-US/kb/profile-manager-create-remove-switch-firefox-profiles

        wd = webdriver.Chrome(options=self._options(), executable_path=self._exe_path or EXECUTABLE_PATH)
        wd.execute_cdp_cmd("Network.setBlockedURLs", {"urls": self._blocked_urls()})
        wd.execute_cdp_cmd("Network.enable", {})
        wd.set_window_size(1280, 960)

        if self._use_proxy:
            if not self._proxy_session:
                raise ValueError('no proxy session')

            wd.proxy = Proxy.get(self._proxy_session)

        return wd

    def _options(self):
        opts = webdriver.ChromeOptions()

        if self._headless:
            opts.headless = True

        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.{random.randint(0, 99)} Safari/537.36"
        )
        opts.add_argument(f'--user-data-dir={USER_DATA_DIR}')
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-infobars")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-browser-side-navigation")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--ignore-certificate-errors")
        # opts.add_argument('--proxy-server=%s' % '192.168.10.242:3488')

        return opts

    @staticmethod
    def _blocked_urls():
        return [
            "t.karte.io",
            "karte.io",
            "gum.criteo.com",
            "t.co",
            "o.imgz.jp",
            "s.go-mpulse.net",
            "cdn.optimizely.com",
            "im-apps.net",
            'doubleclick.net',
            '*.doubleclick.net',
            '*.g.doubleclick.net',
            '*.g.doubleclick.net',
            "c.imgz.jp",  # 禁止图片
            # 'www.google-analytics.com',
            # 'www.google.com',
            # 'google.com',
            # 'www.google.co.jp',
            # '*google*',
            'twitter.com',
            'analysics.twitter.com',
            'www.googletagmanager.com',
            'b0.yahoo.co.jp',
            'yjtag.yahoo.co.jp',

            '*.hdslb.com',
        ]

    # @staticmethod
    # def _proxy():
    #     return {
    #         "http": "http://rhvkc4u_psd-zone-custom-region-jp:ebDX4yxxy7@proxy.ipidea.io:2333",
    #         "https": "http://rhvkc4u_psd-zone-custom-region-jp:ebDX4yxxy7@proxy.ipidea.io:2333",
    #     }


class Proxy:
    @staticmethod
    def get(session=0):
        ch = session % 30
        url = f'http://lum-customer-c_0a7a4b19-zone-pa{ch}-country-jp:qo2rrrqhwyxd@zproxy.lum-superproxy.io:22225'
        # url = f'http://rhvkc4u_psd-zone-custom-region-jp-session-{session}:ebDX4yxxy7@proxy.ipidea.io:2334'
        # url = f'http://rhvkc4u_psd-zone-sto322568-region-jp-session-{session}-sessTime-30:ebDX4yxxy7@proxy.ipidea.io:2334'
        # url = f'http://rhvkc4u_psd-zone-sto322568-region-jp-session-plaacc{session}-sessTime-1:ebDX4yxxy7@proxy.ipidea.io:2334'
        # url = 'http://rhvkc4u_psd-zone-custom-region-jp:ebDX4yxxy7@proxy.ipidea.io:2334'
        # url = 'http://rhvkc4u_psd-zone-sto322568-region-jp-sessTime-1:ebDX4yxxy7@proxy.ipidea.io:2334'
        # url = 'http://rhvkc4u_psd-zone-quark-region-jp-sessTime-1:ebDX4yxxy7@proxy.ipidea.io:2334'
        return {"http": url, "https": url}

    @classmethod
    def refresh_ip(cls, account_id, with_retry=False):
        if 'ipidea' in cls.get().get('http', ''):
            return

        try:
            cls.__refresh_ip_ip(account_id, with_retry)
        except RetryError:
            pass

    @classmethod
    @retry(retry_on_result=bool, stop_max_attempt_number=5)
    def __refresh_ip_ip(cls, account_id, with_retry=False):
        data = {'zone': f'pa{account_id}'}
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer 04bbffd7-a1f2-4eb9-b582-66169fa565fd'}
        resp = requests.post('https://luminati.io/api/zone/ips/refresh', json=data, headers=headers)
        if not with_retry:
            return False

        new_ip = resp.json()['new_ips'][0]
        # ip24 = new_ip[: new_ip.rindex('.')]
        return new_ip in cls.ip_blacklist()

    @staticmethod
    def ip_blacklist():
        ip_blacklist = set()
        try:
            with open(IP_BLACKLIST_FILE, 'r') as f:
                for line in f:
                    if not line:
                        continue
                    ip_blacklist.add(line.strip())
        except FileNotFoundError:
            pass

        return ip_blacklist

    @classmethod
    def add_blacklist_ip(cls, ip):
        # ip24 = ip[: ip.rindex('.')]
        if ip in cls.ip_blacklist():
            return

        with open(IP_BLACKLIST_FILE, 'a') as f:
            f.write(ip + '\r\n')
