# sms_utils.py
from twilio.rest import Client

ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxx"
AUTH_TOKEN = "dxxxxxxxxxxxxxxxxxxxxxxxxxx"
FROM_NUMBER = "+11234567890"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_sms(message, to):
    client.messages.create(
        body=message,
        from_=FROM_NUMBER,
        to=to
    )
