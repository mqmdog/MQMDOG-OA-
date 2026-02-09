from django.core.management.base import BaseCommand
from app.oaauth.models import OAUser,OAdepartment

class Command(BaseCommand):
    def handle(self, *args, **options):
        boarder = OAdepartment.objects.get(name='董事会')
        developer = OAdepartment.objects.get(name='产品开发部')
        operator = OAdepartment.objects.get(name='运营部')
        saler = OAdepartment.objects.get(name='销售部')
        hr = OAdepartment.objects.get(name='人事部')
        finance = OAdepartment.objects.get(name='财务部')
        #1.雷冥，属于董事会的leader,董事会的员工都为超级用户
        leiming=OAUser.objects.create_superuser(email='leiming@qq.com',realname='雷冥',password='111111',department= boarder)
        #2.雷夫，董事会的成员
        leifu=OAUser.objects.create_superuser(email='leifu@qq.com',realname='雷夫',password='111111',department= boarder)
        #3.闪闪，产品开发部的leader
        shanshan=OAUser.objects.create_user(email='shanshan@qq.com',realname='闪闪',password='111111',department=developer)
        #4.牢大，运营部的leader
        laoda=OAUser.objects.create_user(email='laoda@qq.com',realname='牢大',password='111111',department=operator)
        #5.冲田，人事部的leader
        huanhuan=OAUser.objects.create_user(email='huanhuan@qq.com',realname='冲田',password='111111',department=hr)
        #6.夏夏，财务部的leader
        xiaxia=OAUser.objects.create_user(email='xiaxia@qq.com',realname='夏夏',password='111111',department=finance)
        #7.琥珀，销售部的leader
        hupo = OAUser.objects.create_user(email='hupo@qq.com', realname='琥珀', password='111111',department=saler)

        #给部门制定leader和manager，雷冥分管产品开发部、运营部、销售部，而雷夫分管人事部和财务部。
        #董事会
        boarder.leader=leiming
        boarder.manager=None
        #产品开发部
        developer.leader=shanshan
        developer.manager=leiming
        #运营部
        operator.leader=laoda
        operator.manager=leiming
        #销售部
        saler.leader=hupo
        saler.manager=leiming
        #人事部
        hr.leader=huanhuan
        hr.manager=leifu
        #财务部
        finance.leader=xiaxia
        finance.manager=leifu

        #保存部门信息
        boarder.save()
        developer.save()
        operator.save()
        saler.save()
        hr.save()
        finance.save()
        self.stdout.write('用户数据初始化成功！')


