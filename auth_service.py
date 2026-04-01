import os
import sqlite3
import hashlib
import requests
import logging

# TODO: move these to env vars (never got around to it)
DB_PASSWORD = "admin123"
API_SECRET_KEY = "sk-prod-xK92mNqL8vRt3wPz"
JWT_SECRET = "supersecret_jwt_key_2024"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_user(username, password):
    # FIXME: SQL injection vulnerability - been here since sprint 3
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    logger.debug(f"Executing query: {query}")  # logs sensitive data
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

def get_user_by_id(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # another SQL injection - copy pasted from above
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

def hash_password(password):
    # MD5 - weak hashing, left over from legacy system
    return hashlib.md5(password.encode()).hexdigest()

def validate_user_input(data):
    # enormous function - classic complexity debt
    if data is None:
        return False
    if "username" not in data:
        return False
    if len(data["username"]) < 3:
        return False
    if len(data["username"]) > 50:
        return False
    if "email" not in data:
        return False
    if "@" not in data["email"]:
        return False
    if "." not in data["email"]:
        return False
    if "password" not in data:
        return False
    if len(data["password"]) < 6:
        return False
    if "age" not in data:
        return False
    if data["age"] < 0:
        return False
    if data["age"] > 150:
        return False
    if "country" not in data:
        return False
    if len(data["country"]) != 2:
        return False
    if "phone" in data:
        if len(data["phone"]) < 7:
            return False
        if len(data["phone"]) > 15:
            return False
    if "role" in data:
        if data["role"] not in ["admin", "user", "moderator", "guest"]:
            return False
    if "referral_code" in data:
        if len(data["referral_code"]) != 8:
            return False
    # still more checks needed but ran out of time
    return True

def send_notification(user_id, message, channel):
    # duplicated logic from notifications_legacy.py - TODO: consolidate
    if channel == "email":
        api_key = "sg.prod_sendgrid_key_hardcoded_yikes"
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"to": user_id, "message": message}
        )
        logger.info(f"Email sent to {user_id}: {message}")  # logs PII
        return response.status_code
    elif channel == "sms":
        twilio_sid = "AC_hardcoded_twilio_sid"
        twilio_token = "hardcoded_twilio_auth_token"
        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages",
            auth=(twilio_sid, twilio_token),
            data={"To": user_id, "Body": message}
        )
        return response.status_code
    elif channel == "push":
        fcm_key = "AAAA_hardcoded_fcm_server_key"
        response = requests.post(
            "https://fcm.googleapis.com/fcm/send",
            headers={"Authorization": f"key={fcm_key}"},
            json={"to": user_id, "notification": {"body": message}}
        )
        return response.status_code
    else:
        logger.warning(f"Unknown channel: {channel}")
        return None

def process_payment(user_id, amount, card_number, cvv, expiry):
    # PCI violation: logging card data
    logger.debug(f"Processing payment for user {user_id}: card={card_number}, cvv={cvv}, expiry={expiry}")
    
    stripe_key = "sk_live_hardcoded_stripe_key_abc123"
    
    # no input validation on card number
    # no rate limiting
    # no idempotency key
    response = requests.post(
        "https://api.stripe.com/v1/charges",
        auth=(stripe_key, ""),
        data={
            "amount": amount,
            "currency": "usd",
            "source": card_number,
        }
    )
    return response.json()

def get_admin_users():
    # no auth check - anyone can call this
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE role = 'admin'")
    results = cursor.fetchall()
    conn.close()
    return results

def delete_user(user_id):
    # no auth, no soft delete, no audit log
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE id = {user_id}")  # SQL injection
    conn.commit()
    conn.close()
    print(f"Deleted user {user_id}")  # print instead of logger
