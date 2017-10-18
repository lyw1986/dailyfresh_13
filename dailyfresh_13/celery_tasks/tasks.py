from celery import Celery

import os
os.environ['DJANGO_SETTINGS_MODULE']='dailyfresh_13.settings'

# 放到celery服务器上时将注释打开
# import django
# django.setup()

from django.core.mail import send_mail
from django.conf import settings

app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1/2')

@app.task
def send_active_email(user_name, to_email, token):
    subject = '天天生鲜用户激活'
    body = ''
    sender = settings.EMAIL_FROM
    receivers = [to_email]
    html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                'http://127.0.0.1:8000/users/active/%s<a></p>' % (user_name, token, token) # html邮件体

    send_mail(subject, body, sender, receivers, html_message=html_body)