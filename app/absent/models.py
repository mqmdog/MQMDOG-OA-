from django.db import models  # 导入Django的模型类
from django.contrib.auth import get_user_model  # 导入Django的用户模型

# 获取用户模型，这里重命名为 OAUser
OAUser = get_user_model()


class AbsentStatusChoices(models.IntegerChoices):
    # 审批中
    AUDITING = 1
    # 审核通过
    PASS = 2
    # 审核拒绝
    REJECT = 3


class AbsentType(models.Model):#请假类型
    name = models.CharField(max_length=100) # 请假类型名称
    create_time = models.DateTimeField(auto_now_add=True) # 创建时间


class Absent(models.Model): #请假详情信息
    # 1. 标题
    title = models.CharField(max_length=200)
    # 2. 请假详细内容
    request_content = models.TextField()
    # 3. 请假类型（事假、婚假）
    absent_type = models.ForeignKey(AbsentType, on_delete=models.CASCADE, related_name='absents', related_query_name='absents')
    # 如果在一个模型中，有多个字段对同一个模型引用了外键，那么必须指定related_name为不同的值
    # 4. 发起人
    requester = models.ForeignKey(OAUser, on_delete=models.CASCADE, related_name='my_absents', related_query_name='my_absents')
    # 5. 审批人（可以为空）
    responder = models.ForeignKey(OAUser, on_delete=models.CASCADE, related_name='sub_absents', related_query_name='sub_absents', null=True)
    # 6. 状态
    status = models.IntegerField(choices=AbsentStatusChoices, default=AbsentStatusChoices.AUDITING)
    # 7. 请假开始日期
    start_date = models.DateField()
    # 8. 请假结束日期
    end_date = models.DateField()
    # 9. 请假发起时间
    create_time = models.DateTimeField(auto_now_add=True)
    # 10. 审批回复内容
    response_content = models.TextField(blank=True)

    class Meta:
        ordering = ['-create_time']#按照时间倒序排列