from django.core.mail import send_mail
from django.conf import settings
from OA_back import celery_app




@celery_app.task(name='send_mail_task')
def send_mail_task(email, subject, message):#邮件发送任务
    send_mail(subject, recipient_list=[email] ,message=message,from_email=settings.DEFAULT_FROM_EMAIL)