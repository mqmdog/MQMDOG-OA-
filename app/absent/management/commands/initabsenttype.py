# 导入 Django 管理命令的基类
from django.core.management.base import BaseCommand

# 导入模型类（假设模型位于 app.absent.models 模块中）
from app.absent.models import AbsentType


# 定义自定义命令类，继承自 BaseCommand
class Command(BaseCommand):
    # 命令执行的主方法
    def handle(self, *args, **options):
        # 定义需要创建的请假类型列表（字符串数组）
        absent_types = ["事假", "病假", "工伤假", "婚假", "丧假", "产假", "探亲假", "公假", "年休假"]

        # 创建空列表，用于存放 AbsentType 实例对象
        absents = []

        # 遍历请假类型列表中的每个类型名称
        for absent_type in absent_types:
            # 为每个请假类型创建 AbsentType 模型实例（不立即保存到数据库）
            absents.append(AbsentType(name=absent_type))

        # 使用 bulk_create 方法批量创建记录（一次性将所有实例保存到数据库）
        # bulk_create 比逐条 save() 更高效，减少数据库查询次数
        AbsentType.objects.bulk_create(absents)

        # 在控制台输出成功消息（使用 self.stdout.write 而不是 print 可以更好地处理输出流）
        self.stdout.write('考勤类型数据初始化成功！')