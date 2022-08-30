import os
import time
from collections import namedtuple
from datetime import datetime, timedelta
from typing import List
from urllib.parse import parse_qs, urlparse

from parsel import Selector
from retrying import retry
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    UnexpectedAlertPresentException,
    StaleElementReferenceException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from err import (
    PageNotLoadedError,
    AccessDeniedError,
    ClickNotRespondedError,
    ClickElementNotLoadedError,
    CaptchaNotLoadedError,
    CaptchaIncorrectError,
    GoodsRemovedError,
    NoStockError,
    CartMismatchError,
    LoginTimeoutError,
    OrderNoNotFoundError,
    BadGatewayError,
    error_codes,
    NoGoodsAvailableError,
    AddCartTimeoutError,
    RemoveCartTimeoutError,
    OrderPriceTooLowError,
)

Account = namedtuple("Account", ["login_name", "password", "address"])
CreditCard = namedtuple("CreditCard", ["no", "code", "valid_month", "valid_year"])
OrderItem = namedtuple('OrderItem', ['alias', 'extract'])


class Goods:
    def __init__(self, shop_link_name, goods_platform_id, goods_sku_platform_id, quantity, cancellation_reason=0):
        self.shop_link_name = shop_link_name
        self.goods_platform_id = goods_platform_id
        self.goods_sku_platform_id = goods_sku_platform_id
        self.quantity = quantity
        self.cancellation_reason = cancellation_reason

    def __str__(self):
        return str(self.__dict__)


class RobotMixin:
    def __init__(self, driver):
        self.__driver = driver

    @retry(
        retry_on_exception=lambda e: isinstance(e, (PageNotLoadedError, AccessDeniedError, BadGatewayError)),
        stop_max_attempt_number=3,
    )
    def _load_with_retry(self, url, presence=None, presence_timeout=20, page_timeout=40, script_timeout=20):
        return self._load(url, presence, presence_timeout, page_timeout, script_timeout)

    def _load(self, url, presence=None, presence_timeout=20, page_timeout=40, script_timeout=20):
        self._set_timeout(page_timeout, script_timeout)

        try:
            self.__driver.get(url)
        except TimeoutException:
            if not presence:
                self._set_timeout()
                raise PageNotLoadedError(url)

        raise PageNotLoadedError(url)

        h1 = self._find_element_safe(By.CSS_SELECTOR, "div[class='header-login-entry']")
        if h1:
            if h1.text == 'Access Denied':
                raise AccessDeniedError(url)
            if h1.text == 'Bad Gateway Error':
                raise BadGatewayError(url)

        self._set_timeout()

        if presence:
            try:
                ActionChains(self.__driver).move_to_element(h1).perform()
                down_data_click = WebDriverWait(self.__driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div[class='login-btn']"))
                )

                return WebDriverWait(self.__driver, timeout=presence_timeout).until(
                    EC.presence_of_element_located(presence)
                )
            except TimeoutException:
                raise PageNotLoadedError(url)

    @retry(
        retry_on_exception=lambda e: isinstance(e, ClickNotRespondedError),
        stop_max_attempt_number=2,
    )
    def _click_with_retry(self, element, presence=None, presence_timeout=20, page_timeout=40, script_timeout=20):
        self._click(element, presence, presence_timeout, page_timeout, script_timeout)

    def _click(self, element, presence=None, presence_timeout=20, page_timeout=40, script_timeout=20):
        self._set_timeout(page_timeout, script_timeout)

        try:
            WebDriverWait(self.__driver, timeout=presence_timeout).until(EC.presence_of_element_located(element))
        except TimeoutException:
            raise ClickElementNotLoadedError()

        try:
            e = self.__driver.find_element(*element)
            e.click()
        except TimeoutException:
            if not presence:
                self._set_timeout()
                raise ClickNotRespondedError()

        h1 = self._find_element_safe(By.CSS_SELECTOR, "h1")
        if h1:
            if h1.text == 'Access Denied':
                raise AccessDeniedError()
            if h1.text == 'Bad Gateway Error':
                raise BadGatewayError()

        self._set_timeout()

        if presence:
            try:
                return WebDriverWait(self.__driver, timeout=presence_timeout).until(
                    EC.presence_of_element_located(presence)
                )
            except TimeoutException:
                raise ClickNotRespondedError()

    def _set_timeout(self, page_timeout=90, script_timeout=30):
        self.__driver.set_page_load_timeout(page_timeout)
        self.__driver.set_script_timeout(script_timeout)

    def _find_element_safe(self, *args, **kwargs):
        try:
            return self.__driver.find_element(*args, **kwargs)
        except NoSuchElementException:
            return None

    @staticmethod
    def _input(element, value):
        element.clear()
        element.send_keys(value)


class CartItemCollector:
    CART_URL = "https://zozo.jp/_cart/default.html"

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.driver.get(self.CART_URL)
        WebDriverWait(self.driver, timeout=30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section#cartMain"))
        )
        self.selector = Selector(text=self.driver.page_source)

    def collect(self) -> dict:
        r = {}
        for n in self.selector.css("section#cartMain tr[data-live-engage-sku]:not([data-live-engage-sku=''])"):
            sku = int(n.attrib.get("data-live-engage-sku", 0))
            quantity = int(n.css('div[data-live-engage="quantity"]::text').extract_first("0"))

            if sku in r:
                r[sku] += quantity
            else:
                r[sku] = quantity

        return r


class Robot(RobotMixin):
    HOMEPAGE_URL = "https://www.bilibili.com/"
    # MEMBER_URL = "https://zozo.jp/_member/default.html"
    # LOGIN_URL = "https://zozo.jp/_member/login.html"
    # GOODS_DETAIL_URL = "https://zozo.jp/shop/{shop_link_name}/goods/{goods_platform_id}/"
    # ORDER_LIST_URL = "https://zozo.jp/_member/orderhistory/default.html"
    # ORDER_DETAIL_URL = (
    #     "https://zozo.jp/_member/orderhistory/detail.html?oid={platform_order_no}&isold=&ohtype=1&ohterm=2&ohid="
    # )

    DEFAULT_SCREENSHOT_ROOT_PATH = r"/Users/hh/Downloads/"

    def __init__(self, driver, account: Account, credit_card=None, screenshot_root_path=None, log_id=None):
        self.driver = driver
        self.account = account
        self.credit_card = credit_card
        self.screenshot_root_path = screenshot_root_path or self.DEFAULT_SCREENSHOT_ROOT_PATH
        self.log_id = log_id

        self.screenshot_prefix = "%s-%s" % (
            self.account.login_name.replace("@", "_"),
            datetime.now().strftime("%Y_%m_%d_%H.%M.%S"),
        )
        self.screenshot_seq = 0

        super(Robot, self).__init__(driver)
        self._set_timeout()

    def _ensure_login(self):
        presence = (By.CSS_SELECTOR, "div.header-avatar-wrap--container.mini-avatar--small")
        try:
            return self._load(self.HOMEPAGE_URL, presence=presence, page_timeout=30, presence_timeout=10)
        except PageNotLoadedError:
            self._login(presence=presence)

    @retry(
        retry_on_exception=lambda e: isinstance(e, (CaptchaNotLoadedError, CaptchaIncorrectError)),
        stop_max_attempt_number=1,
    )
    def _login(self, presence):
        self._take_screenshot("login")

        WebDriverWait(self.driver, timeout=5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='header-login-entry']"))
        )
        login_entry_element = self._find_element_safe(By.CSS_SELECTOR, "div[class='header-login-entry']")
        ActionChains(self.driver).move_to_element(login_entry_element).perform()
        login_btn = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[class='login-btn']"))
        )
        login_btn.click()
        time.sleep(5)
        # ActionChains(self.driver).move_to_element(login_entry_element).perform()
        e = self._find_element_safe(By.CSS_SELECTOR, "div[class='bili-mini-account'] > input[placeholder='请输入账号']")
        if not e:
            raise LoginTimeoutError()

        self._input(e, self.account.login_name)

        e = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入密码']")
        self._input(e, self.account.password)

        # e = self._find_element_safe(By.CSS_SELECTOR, "input[id=captcha_text]")
        # if e:
        #     self._take_screenshot("captcha", log_tag=1)
        #
        #     try:
        #         captcha_img = (By.CSS_SELECTOR, "div[id=div_captcha] img")
        #         WebDriverWait(self.driver, timeout=30).until(EC.presence_of_element_located(captcha_img))
        #     except TimeoutException:
        #         self.driver.refresh()
        #         raise CaptchaNotLoadedError()
        #
        #     img_file = self.driver.find_element(*captcha_img).screenshot_as_png
        #
        #     # try:
        #     #     captcha_text = recognize_captcha(img_file)
        #     # except twocaptcha.api.NetworkException:
        #     #     captcha_text = recognize_captcha_2(img_file)
        #
        #     if captcha_text:
        #         self._input(e, captcha_text)
        #     else:
        #         self.driver.refresh()
        #         raise CaptchaNotInputtedError(self.account.login_name)

        try:
            self._click(
                (By.CSS_SELECTOR, '.universal-btn.login-btn'),
                presence=presence,
                page_timeout=45,
                presence_timeout=10,
            )
        except ClickNotRespondedError:
            if self._find_element_safe(By.CSS_SELECTOR, 'p[class=p-member-login__error]'):  # 验证码错误
                self.driver.refresh()
                raise CaptchaIncorrectError()

            raise LoginTimeoutError(self.account.login_name)

    def create_order(self, goods_list: List[Goods], allow_partial_order=False):
        """创建订单"""
        self._ensure_login()
        return self._create_order0(goods_list, allow_partial_order)

    def _create_order0(self, goods_list: List[Goods], allow_partial_order=False):
        self._clean_cart()

        skipped_goods = []

        for goods in goods_list:
            ok, reason = self._add_goods_into_cart(goods, allow_partial_order)
            if not ok:
                goods.cancellation_reason = reason
                skipped_goods.append(goods)

        self._check_cart(goods_list, skipped_goods)

        platform_order_no = self._submit_order()
        return {
            'platform_order_no': platform_order_no,
            'skipped_goods': [g.__dict__ for g in skipped_goods],
            'platform_goods_amount': 0,
            'platform_order_amount': 0,
        }

    def _add_goods_into_cart(self, goods: Goods, allow_partial_order) -> (bool, int):
        for _ in range(goods.quantity):
            try:
                self._add_cart(goods)
            except (GoodsRemovedError, NoStockError) as e:
                if not allow_partial_order:
                    raise

                return False, error_codes[type(e)]

        return True, 0

    def _add_cart(self, cart_item: Goods):
        self.load_goods_detail_page(cart_item)

        e = self._find_element_safe(
            By.CSS_SELECTOR,
            f"li#cart_did_{cart_item.goods_sku_platform_id} div.p-goods-add-cart__action",
        )
        if not e:
            raise GoodsRemovedError(cart_item)

        e = self._find_element_safe(
            By.CSS_SELECTOR,
            f"li#cart_did_{cart_item.goods_sku_platform_id} div.p-goods-add-cart__action span.c-button__label-main",
        )
        if not e or e.text.strip() == "予約する":
            raise NoStockError(cart_item)

        add_btn = (
            By.CSS_SELECTOR,
            f"li#cart_did_{cart_item.goods_sku_platform_id} div.p-goods-add-cart__action form button[type=submit]",
        )
        e = self._find_element_safe(*add_btn)
        if not e:
            raise NoStockError(f"no stock: {cart_item}")

        self.add_goods_to_cart(add_btn)

    def load_goods_detail_page(self, goods: Goods):
        try:
            self._load_with_retry(
                self._goods_detail_page_url(goods),
                (By.CSS_SELECTOR, "div.blockMain dl.p-goods-information-action"),
                page_timeout=30,
                presence_timeout=10,
            )
        except PageNotLoadedError:
            if self._find_element_safe(By.CSS_SELECTOR, "div[class=p-goods-nogoods-header]"):
                raise GoodsRemovedError(goods)

            raise

    @classmethod
    def _goods_detail_page_url(cls, goods: Goods):
        return cls.GOODS_DETAIL_URL.format(
            shop_link_name=goods.shop_link_name,
            goods_platform_id=goods.goods_platform_id,
        )

    @retry(retry_on_exception=lambda e: isinstance(e, AddCartTimeoutError), stop_max_attempt_number=2)
    def add_goods_to_cart(self, add_button):
        try:
            self._click(
                add_button, presence=(By.CSS_SELECTOR, "section#cartMain"), presence_timeout=10, page_timeout=30
            )
        except UnexpectedAlertPresentException:
            pass
        except ClickNotRespondedError:
            self.driver.refresh()
            raise AddCartTimeoutError()

    def _check_cart(self, goods_list: List[Goods], skipped_goods: List[Goods]):
        goods_items = {v.goods_sku_platform_id: v.quantity for v in goods_list}
        cart_items = CartItemCollector(self.driver).collect().copy()

        for goods in skipped_goods:
            if goods.goods_sku_platform_id in cart_items:
                cart_items[goods.goods_sku_platform_id] += goods.quantity
            else:
                cart_items[goods.goods_sku_platform_id] = goods.quantity

        if goods_items != cart_items:
            self._take_screenshot()
            raise CartMismatchError(
                f'goods_list={[g.__dict__ for g in goods_list]}, skipped_goods={[g.__dict__ for g in skipped_goods]}. '
                f'{goods_items=}, {cart_items=}'
            )

        if len(goods_list) == len(skipped_goods):
            raise NoGoodsAvailableError()

        price_element = self.driver.find_element(By.CSS_SELECTOR, "p[id=totalPrice]")
        order_price = self.__format_price(price_element.text)
        if skipped_goods and order_price < 2250:  # 相当于中国售卖价 199
            raise OrderPriceTooLowError()

    @retry(
        retry_on_exception=lambda e: isinstance(e, (RemoveCartTimeoutError, TimeoutException)),
        stop_max_attempt_number=2,
    )
    def _clean_cart(self):
        self._refresh_cart()
        time.sleep(5)

        elements = self.driver.find_elements(By.CSS_SELECTOR, "section#cartMain td.delete a")
        for _ in range(len(elements)):
            elements = self.driver.find_elements(By.CSS_SELECTOR, "section#cartMain td.delete a")
            if not elements:
                break

            self._set_timeout(page_timeout=30)
            try:
                elements[0].click()
            except TimeoutException:
                self._refresh_cart()
                raise RemoveCartTimeoutError()
            finally:
                self._set_timeout()

            try:
                WebDriverWait(self.driver, 3).until(EC.alert_is_present())
                alert = self.driver.switch_to.alert
                alert.accept()
            except TimeoutException:
                pass

            self._refresh_cart()

    def _refresh_cart(self):
        try:
            self._load_with_retry(
                CartItemCollector.CART_URL,
                presence=(By.CSS_SELECTOR, "section#cartMain"),
                page_timeout=30,
                presence_timeout=10,
            )
        except UnexpectedAlertPresentException:
            pass

    def _submit_order(self):
        self.driver.find_element(
            By.CSS_SELECTOR,
            "section#cartNext input[type=submit]",
        ).click()

        confirm_btn = (By.CSS_SELECTOR, "div#confirmation div a.confirmBtn")
        customer_info_css = "section#customerInfo p.note a"

        # 如果有必要，更新选择地址、信用卡
        self._ensure_order(presence=confirm_btn)

        try:
            self._click(
                confirm_btn, presence=(By.CSS_SELECTOR, customer_info_css), presence_timeout=20, page_timeout=90
            )
        except ClickNotRespondedError:
            self._take_screenshot('conform_order')
            # alarm(f'（重要）[{self.log_id}] 下单成功但订单号缺失', AlarmLevel.ALARM_TYPE_SERIOUS)
            raise OrderNoNotFoundError(self.log_id)

        url = self.driver.find_element(By.CSS_SELECTOR, customer_info_css).get_attribute("href")
        return parse_qs(urlparse(url).query)["oid"][0]

    def _ensure_order(self, presence):
        goto_next_btn = "div#goToNext input[type=submit]"
        if not self._find_element_safe(By.CSS_SELECTOR, goto_next_btn):
            return

        self._select_address()

        delivery_time_btn = "div#registAddress label[for=deliveryDayTime]"
        e = self._find_element_safe(By.CSS_SELECTOR, delivery_time_btn)
        if e:
            try:
                e.click()
                time.sleep(2)
            except StaleElementReferenceException:
                pass

        creditcard_btn = "div#paymentForm label[for=creditcard]"
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, creditcard_btn),
            )
        )
        self.driver.find_element(By.CSS_SELECTOR, creditcard_btn).click()

        select_card_btn = self._find_element_safe(By.CSS_SELECTOR, "div[id=paymentForm] dd[class=registedCard] label")
        if select_card_btn:
            time.sleep(5)
            select_card_btn.click()

            card_radio = "dd.registedCard label.trigger"
            WebDriverWait(self.driver, timeout=20).until(EC.presence_of_element_located((By.CSS_SELECTOR, card_radio)))
            e = self.driver.find_element(By.CSS_SELECTOR, card_radio)
            e.click()
            e.send_keys(Keys.TAB)

            card_input = 'div#paymentForm dl[class="securtyCode clearfix"] input'
            WebDriverWait(self.driver, timeout=20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, card_input),
                )
            )
            e = self.driver.find_element(By.CSS_SELECTOR, card_input)
            time.sleep(3)
            self._input(e, self.credit_card.code)
        else:
            card_input = "div#paymentForm input[name=cn_normal]"
            WebDriverWait(self.driver, timeout=20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, card_input),
                )
            )

            self._input(self.driver.find_element(By.CSS_SELECTOR, card_input), self.credit_card.no)

            card_input = "div#paymentForm input[name=scn_normal]"
            self._input(self.driver.find_element(By.CSS_SELECTOR, card_input), self.credit_card.code)

            card_input = "div#paymentForm select[name=em_normal]"
            Select(self.driver.find_element(By.CSS_SELECTOR, card_input)).select_by_value(self.credit_card.valid_month)

            card_input = "div#paymentForm select[name=ey_normal]"
            Select(self.driver.find_element(By.CSS_SELECTOR, card_input)).select_by_value(self.credit_card.valid_year)

            time.sleep(3)

            # creditcard_btn = "div#paymentForm label[for=rgist_normal] span.checkbox"
            # self.driver.find_element(By.CSS_SELECTOR, creditcard_btn).click()

        self._click_with_retry(
            element=(By.CSS_SELECTOR, goto_next_btn),
            presence=presence,
            page_timeout=60,
            presence_timeout=10,
        )

    def _select_address(self):
        address_list = self.driver.find_elements(By.CSS_SELECTOR, "dl#addCheck dd.close")
        if self.account.address >= len(address_list):
            address_list[-1].click()
        else:
            address_list[self.account.address].click()

    def fetch_logistics(self, platform_order_nos):
        self._ensure_login()

        logistics_nos = {}
        for order_no in platform_order_nos:
            logistics_nos[order_no] = self.__fetch_logistics(order_no)

        return logistics_nos

    def __fetch_logistics(self, platform_order_no):
        try:
            self._load_with_retry(
                self.ORDER_DETAIL_URL.format(platform_order_no=platform_order_no),
                page_timeout=30,
            )
        except PageNotLoadedError:
            print(f'{platform_order_no}: page load failed')
            return {}

        try:
            e = self.driver.find_element(By.XPATH, "//th[contains(text(), '伝票番号')]/following-sibling::td")
            merged = self._find_element_safe(By.XPATH, "//th[contains(text(), 'まとめて発送')]")
            return {'platform_logistics_no': e.text, 'package_merged': bool(merged)}
        except NoSuchElementException:
            return {}

    def fetch_orders(self):
        self._ensure_login()

        urls = self.__get_order_urls(self.ORDER_LIST_URL + '?ohtype=2')
        urls.extend(self.__get_order_urls(self.ORDER_LIST_URL + '?ohtype=1&ohterm=1'))
        return [self.__fetch_order_details(url) for url in urls]

    def __get_order_urls(self, start_url):
        self.driver.get(start_url)
        WebDriverWait(self.driver, timeout=40).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article span.tabActive"))
        )

        urls = []
        while True:
            for e in self.driver.find_elements(By.CSS_SELECTOR, "table.orderDetail td.orderTime a.btnS"):
                urls.append(e.get_attribute("href"))

            next_page = self._find_element_safe(By.CSS_SELECTOR, 'div[class*="pager_bottom"] li[class="next"] a')
            if not next_page:
                break

            self.driver.get(next_page.get_attribute("href"))
            WebDriverWait(self.driver, timeout=20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article span.tabActive"))
            )

        return urls

    def __fetch_order_details(self, order_url):
        self.driver.get(order_url)
        WebDriverWait(self.driver, timeout=40).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.contBody"),
            )
        )

        selector = Selector(text=self.driver.page_source)
        trs = selector.css('div[class="sectionInner"] tr')
        order_items = {
            tr.css('th::text').get().strip(): tr.css('td') for tr in trs if tr.attrib.get('class') != 'thumbBox detail'
        }
        order_goods = [tr.css('td') for tr in trs if tr.attrib.get('class') == 'thumbBox detail']

        order_item_needs = {
            '配送状況': OrderItem(
                alias='status',
                extract=lambda x: self.__extract_status(x),
            ),
            '注文番号': OrderItem(
                alias='platform_order_no',
                extract=lambda x: x.css('::text').get().strip(),
            ),
            '注文日': OrderItem(
                alias='order_time',
                extract=lambda x: (
                    datetime.strptime(x.css('::text').get().strip(), "%Y/%m/%d %H:%M:%S") - timedelta(hours=1)
                ).strftime('%Y-%m-%d %H:%M:%S'),
            ),
            '配達指定日時': OrderItem(
                alias='specified_sending_time',
                extract=lambda x: x.css('::text').get().strip(),
            ),
            '伝票番号': OrderItem(
                alias='platform_logistics_no',
                extract=lambda x: x.css('::text').get('').strip() if x else '',
            ),
            '商品合計': OrderItem(
                alias='total_goods_price',
                extract=lambda x: self.__format_price(x.css('::text').get().strip()) if x else 0,
            ),
            '支払い金額': OrderItem(
                alias='order_price',
                extract=lambda x: self.__format_price(x.css('::text').get().strip()) if x else 0,
            ),
        }
        result = {item.alias: item.extract(order_items.get(name)) for name, item in order_item_needs.items()}
        result['goods'] = [self.__extract_goods(goods) for goods in order_goods]
        return result

    @staticmethod
    def __extract_status(elem):
        text = elem.css('::text').get('').strip()
        codes = {
            '発送済み': 3,
            '配達完了': 5,
            'キャンセル済み': 10,
            '発送後キャンセル': 11,
        }
        if text in codes:
            return codes[text]

        try:
            return elem.css('div[class*="delivery-info__status"]').attrib['data-step']
        except KeyError:
            return 0

    @classmethod
    def __extract_goods(cls, elem):
        goods_sku_platform_id = int(elem.css('p[class="itemName"]>a').attrib['href'].split('did=')[-1].strip())
        price = cls.__format_price(elem.css('span[class="priceNum"]::text').get().strip())
        quantity = int(elem.css('span[class="tax"]::text').get().strip().split('：')[-1])
        remark = elem.css('p[class*="att"]>span::text').get('')
        return {
            'goods_sku_platform_id': goods_sku_platform_id,
            'price': price,
            'quantity': quantity,
            'remark': remark,
        }

    @staticmethod
    def __format_price(price):
        return int(price.replace('¥', '').replace(',', ''))

    def _take_screenshot(self, suffix="", log_tag=0):
        suffix = ("-" + suffix) if suffix else ""
        name = self._screenshot_name(suffix)
        path = os.path.join(self.screenshot_root_path, "screenshot", datetime.now().strftime("%Y-%m-%d"), name)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        self.driver.save_screenshot(path)
        self.screenshot_seq += 1

    def _screenshot_name(self, suffix):
        return "screenshot-%s-%02d%s.png" % (self.screenshot_prefix, self.screenshot_seq, suffix)
