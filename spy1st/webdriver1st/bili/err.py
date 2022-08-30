class PageNotLoadedError(Exception):
    pass


class AccessDeniedError(Exception):
    pass


class BadGatewayError(Exception):
    pass


class ClickNotRespondedError(Exception):
    pass


class ClickElementNotLoadedError(Exception):
    pass


class LoginTimeoutError(Exception):
    pass


class CaptchaNotLoadedError(Exception):
    pass


class CaptchaNotInputtedError(Exception):
    pass


class CaptchaIncorrectError(Exception):
    pass


class GoodsRemovedError(Exception):
    pass


class NoStockError(Exception):
    pass


class CartMismatchError(RuntimeError):
    pass


class OrderNoNotFoundError(Exception):
    pass


class NoGoodsAvailableError(Exception):
    pass


class AddCartTimeoutError(Exception):
    pass


class RemoveCartTimeoutError(Exception):
    pass


class OrderPriceTooLowError(Exception):
    pass


error_codes = {
    CartMismatchError: 1,
    NoStockError: 4,
    GoodsRemovedError: 5,
    LoginTimeoutError: 600,
    PageNotLoadedError: 601,
    AccessDeniedError: 602,
    CaptchaNotLoadedError: 603,
    CaptchaIncorrectError: 604,
    ClickElementNotLoadedError: 605,
    ClickNotRespondedError: 606,
    CaptchaNotInputtedError: 607,
    OrderNoNotFoundError: 608,
    BadGatewayError: 609,
    NoGoodsAvailableError: 610,
    AddCartTimeoutError: 611,
    RemoveCartTimeoutError: 612,
    OrderPriceTooLowError: 613,
}
