from django.db import models
from app.oaauth.models import OAUser, OAdepartment

# 通知
class Inform(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    # 如果前端上传的department_ids中包含了0，比如[0]，那么就认为这个通知是所有部门可见，此时public=True
    public = models.BooleanField(default=False)#是否公开
    author = models.ForeignKey(OAUser, on_delete=models.CASCADE, related_name='informs', related_query_name='informs')
    # departments：序列化的时候用，前端上传部门id，我们通过department_ids来获取
    departments = models.ManyToManyField(OAdepartment, related_name='informs', related_query_name='informs')#可以被那些部门看到
    class Meta:
        ordering = ('-create_time', )

# 什么人什么时间查看过某条通知
class InformRead(models.Model):
    inform = models.ForeignKey(Inform, on_delete=models.CASCADE, related_name='reads', related_query_name='reads')
    user = models.ForeignKey(OAUser, on_delete=models.CASCADE, related_name='reads', related_query_name='reads')
    read_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        # inform和user组合的数据，必须是唯一的
        unique_together = ('inform', 'user')

