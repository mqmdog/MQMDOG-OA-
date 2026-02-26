import os
from celery import Celery #Celery框架核心类，用于创建任务队列实例
from celery.signals import after_setup_logger#Celery日志信号，用于在任务执行时记录日志
import logging#Python标准库，用于日志记录

# 设置django的settings模块，celery会读取这个模块中的配置信息
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OA_back.settings')
# 上下文共享：Celery需要知道Django的配置（数据库、邮件设置、缓存等）
# 模块导入：设置后，Celery可以自动加载Django的settings模块
# 配置统一：避免在两个地方维护相同的配置信息


# 创建celery实例
app = Celery('OA_back')

## 日志管理
@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add filehandler
    fh = logging.FileHandler('celery.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

# 配置从settins.py中读取celery配置信息，所有Celery配置信息都要以CELERY_开头
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务，任务可以写在app/tasks.py中
app.autodiscover_tasks()

# 测试任务
#1.bind=True,在任务函数中，第一个参数就是任务对线（task），如果没有设置这个参数，或者是bind=False,那么任务函数中就不会有任务对象参数
#2.ignore_result=True,任务执行完成后，结果会被celery忽略，就不会保存任务执行的结果
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')