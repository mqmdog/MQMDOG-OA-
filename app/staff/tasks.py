from django.core.mail import send_mail
from django.conf import settings
from OA_back import celery_app

# 将普通函数注册为 Celery 异步任务，name 参数指定任务名称
@celery_app.task(name='send_mail_task')  
def send_mail_task(email, subject, message):#邮件发送任务
    send_mail(subject, recipient_list=[email] , message=message,from_email=settings.DEFAULT_FROM_EMAIL)


# 参数	类型	说明
# subject	str	邮件主题
# message	str	邮件正文
# from_email	str	发件人邮箱（如 noreply@company.com）
# recipient_list	list	收件人邮箱列表

# 调用 send_mail_task.delay(email, subject, message)
#             ↓
#        加入 Celery 队列
#             ↓
#     Worker 进程异步执行
#             ↓
#     调用 Django send_mail() 发送邮件

# 异步发送邮件：避免阻塞主线程
# 可重用性强：任何地方都可以调用 send_mail_task.delay()
# 解耦设计：邮件发送逻辑与业务逻辑分离
