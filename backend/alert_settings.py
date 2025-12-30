# alert_settings.py

ENABLE_EMAIL_ALERTS = False
ENABLE_SMS_ALERTS = False

def get_settings():
    return {
        "email": ENABLE_EMAIL_ALERTS,
        "sms": ENABLE_SMS_ALERTS
    }

def update_settings(email: bool, sms: bool):
    global ENABLE_EMAIL_ALERTS, ENABLE_SMS_ALERTS
    ENABLE_EMAIL_ALERTS = email
    ENABLE_SMS_ALERTS = sms
