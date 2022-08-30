from robot import Account, Goods, CreditCard, Robot
from wd import RobotWebdriver


def create_order():
    cart_items = [
        Goods(shop_link_name="wego", goods_platform_id=55782034, goods_sku_platform_id=94115858, quantity=1, status=0),
    ]
    print(robot.create_order(cart_items))


def fetch_logistics():
    print(robot.fetch_logistics([1125997593, 1129284573]))


def fetch_orders():
    print(robot.fetch_orders())


account = Account(login_name="17862921319", password="Xsbhh150682", address=0)
credit_card = CreditCard(no="", code="", valid_month="03", valid_year="27")
robot = Robot(
    # driver=RobotWebdriver.create_local(ChromeDriverManager().install()),
    driver=RobotWebdriver.create_local(),
    account=account,
    credit_card=credit_card,
)

if __name__ == "__main__":
    fetch_orders()
