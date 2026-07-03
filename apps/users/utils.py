import time
from django.core.mail import send_mail
from django.conf import settings
import secrets


def send_otp_via_email(email, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It is valid for 5 minutes.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
    time.sleep(1) 
    return True



def generate_otp():
    return str(secrets.randbelow(10**4)).zfill(4) 
