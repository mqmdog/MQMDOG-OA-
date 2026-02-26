from rest_framework import serializers
from .models import Inform, InformRead
from app.oaauth.serializer import UserSerializer, DepartmentSerializer
from app.oaauth.models import OAdepartment



class InformReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformRead
        fields = "__all__"


# 通知序列化
class InformSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    departments = DepartmentSerializer(many=True, read_only=True)
    # department_ids：是一个包含了部门id的列表
    # 如果后端要接受列表，那么就需要用到ListField: [1,2]
    department_ids = serializers.ListField(write_only=True)
    reads = InformReadSerializer(many=True, read_only=True)


    class Meta:
        model = Inform
        fields = "__all__"
        read_only_fields = ('public', ) # 只读字段


    # 重写保存Inform对象的create方法
    def create(self, validated_data):
        request = self.context['request']
        # 从验证后的数据中取出 department_ids（创建时传入的部门ID列表）
        department_ids = validated_data.pop("department_ids")
        # department_ids: ['0', '1', '2']
        # 使用 map + lambda 将列表中每个元素转换为 int 类型
        # [ 0, 1, 2 ]  (整数列表)
        department_ids = list(map(lambda value: int(value), department_ids))
        # 判断部门ID列表中是否包含0，如果包含0，则表示该通知是公开的，否则是部门可见的
        if 0 in department_ids:
            # 创建公开通知（public=True）
            inform = Inform.objects.create(public=True, author=request.user, **validated_data)
        else:
            # 创建部门可见通知（public=False）
            # id__in是Django ORM中用于查询主键在给定列表中的对象的查询条件，这里用于查询部门ID在给定列表中的部门对象
            departments = OAdepartment.objects.filter(id__in=department_ids).all()
            inform = Inform.objects.create(public=False, author=request.user, **validated_data)
            inform.departments.set(departments) # 设置通知的部门
            inform.save() # 保存通知对象
        return inform 


# 视图层调用 serializer.save() → DRF 自动调用你重写的 create() 方法 → 完成业务逻辑处理 → 返回数据库对象。
# 前端请求体:
# {
#     "title": "放假通知",
#     "content": "明天放假",
#     "department_ids": ["0"]          ← 前端传入
# }
# ↓
# ┌─────────────────────────────────────────────────────┐
# │  View: InformViewSet.create()                        │
# │         ↓                                           │
# │  Serializer: InformSerializer(data=request.data)    │
# │         ↓                                           │
# │  is_valid() 验证字段                                 │
# │         ↓                                           │
# │  serializer.save() 触发 create()                     │
# │         ↓                                           │
# │  InformSerializer.create(validated_data)           │
# │              ↓                                      │
# │  处理 department_ids = [0, 1, 2]                    │
# │              ↓                                      │
# │  Inform.objects.create(public=True, ...)            │
# └─────────────────────────────────────────────────────┘
# ↓
# 返回响应:
# {
#     "id": 1,
#     "title": "放假通知",
#     "content": "...",
#     "public": true,
#     "author": {...},
#     "departments": [...]
# }

# 标记通知为已读序列化
class ReadInformSerializer(serializers.Serializer):
    inform_pk=serializers.IntegerField(error_messages={"required":"请传入inform的id！"})

