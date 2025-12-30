# alert_service.py
from models import Inventory
from email_utils import send_email
from sms_utils import send_sms
from alert_settings import ENABLE_EMAIL_ALERTS, ENABLE_SMS_ALERTS

ADMIN_EMAIL = "amankgo23@gmail.com"
ADMIN_PHONE = "+917903447986"

def check_stock_and_alert(db):
    items = db.query(Inventory).all()

    for item in items:
        stock = item.current_stock

        if stock == 0:
            status = "STOCKOUT"
        elif stock < 20:
            status = "UNDERSTOCK"
        elif stock > 500:
            status = "OVERSTOCK"
        else:
            continue

        message = (
            f"⚠ Stock Alert\n"
            f"Item: {item.family}\n"
            f"Store: {item.store_nbr}\n"
            f"Stock: {stock}\n"
            f"Status: {status}"
        )

        # 📧 EMAIL (TOGGLE CONTROLLED)
        if ENABLE_EMAIL_ALERTS:
            send_email(
                subject=f"{status} Alert - {item.family}",
                body=message,
                to_email=ADMIN_EMAIL
            )

        # 📱 SMS (TOGGLE CONTROLLED)
        if ENABLE_SMS_ALERTS:
            send_sms(message, ADMIN_PHONE)
