from seleniumwire import webdriver as seleniumwire_webdriver

from pyutil.program.python import merge_dicts

default_prefs = {}


class Webdriver:
    """
    用于爬虫的WebDriver
    """

    _image_exts = (".png", ".jpg", ".gif", ".svg", ".ico")

    _exclude_hosts = (
        "cdn.optimizely.com",
        "s.go-mpulse.net",
        "www.googletagmanager.com",
        "rtm-tracking.zozo.jp",
        "s.yjtag.jp",
        "o.imgz.jp",  # 禁止图片
        "c.imgz.jp",  # 禁止图片
        "t.karte.io",
        "karte.io",
        "gum.criteo.com",
        "t.co",
        "im-apps.net",
    )

    def __init__(self, proxy):
        self.proxy = proxy

    @classmethod
    def create(cls, proxy=True):
        return cls(proxy)._create0()

    def _create0(self):
        # wd = seleniumwire_webdriver.Firefox(
        #     firefox_profile=webdriver.FirefoxProfile("/home/appuser/firefox-profile-spider"),
        #     options=self._options(),
        #     seleniumwire_options=self._seleniumwire_options(),
        # )
        # wd.proxy = self._proxy()

        wd = seleniumwire_webdriver.Chrome(executable_path="/Users/hh/Documents/tools_using/chromedriver")
        wd.proxy = self._proxy()

        return wd

    def _proxy(self):
        return {
            "http": "http://rhvkc4u_psd-zone-custom-region-jp:ebDX4yxxy7@proxy.ipidea.io:2333",
            "https": "http://rhvkc4u_psd-zone-custom-region-jp:ebDX4yxxy7@proxy.ipidea.io:2333",
        }

    def _options(self):
        opts = seleniumwire_webdriver.FirefoxOptions()
        opts.headless = True

        prefs = {
            "permissions.default.stylesheet": 2,
            "permissions.default.image": 2,
            "javascript.enabled": False,
        }
        prefs = merge_dicts(default_prefs, prefs)
        for k, v in prefs.items():
            opts.set_preference(k, v)

        return opts

    def _seleniumwire_options(self):
        return {
            "disable_capture": True,
            "disable_encoding": True,
            "connection_keep_alive": True,
            "verify_ssl": False,
            "ignore_http_methods": ["OPTIONS", "POST"],
            "exclude_hosts": self._exclude_hosts,
        }
