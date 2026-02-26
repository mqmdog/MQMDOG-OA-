from rest_framework.views import APIView
from app.inform.models import Inform, InformRead
from app.inform.serializer import InformSerializer
from django.db.models import Q #构建复杂的OR/AND逻辑条件
from django.db.models import Prefetch #优化数据库查询，预加载相关数据（比JOIN更灵活）
from rest_framework. response import Response
from app.absent.models import Absent
from app.absent.serializer import AbsentSerializer
from app.oaauth.models import OAdepartment
from django.db.models import Count #聚合计数
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator


# @cache_page(60*15)
# def cache_demo_view(request):
#     pass

#返回当前登录用户能看到的最新10条通知。
class LatestInformView(APIView):
    """
    返回最新的10条通知
    """
   # @method_decorator(cache_page(30))#缓存设置为30秒
    def get(self, request):
        current_user = request.user
        # 返回公共的，或者是我所在的部门能看到的通知
        informs = Inform.objects.prefetch_related(Prefetch("reads", queryset=InformRead.objects.filter(user_id=current_user.uid)), 'departments').filter(Q(public=True) | Q(departments=current_user.department))[:10]
        serializer = InformSerializer(informs, many=True)
        return Response(serializer.data)


# 假设没有Prefetch，而是直接访问
# inform.reads.all()：
# Django会对每条通知执行一次SQL查询来获取InformRead记录
# 10条通知 = 10次额外的SQL查询（N + 1问题）
# 用了Prefetch后的优化：
# 第1次查询：获取10条Inform记录
# 第2次查询：一次性获取这10条通知的所有InformRead记录，且过滤条件是
# user_id = 当前用户ID
# Django自动将结果关联回Inform对象的.reads属性
# 总共只有2次数据库查询
# 相关参数讲解：
# queryset = InformRead.objects.filter(user_id=current_user.uid)：只获取当前用户的阅读记录（剔除其他用户的记录，节省内存）
#'departments'：简写，表示普通的预加载（不需要过滤）


#返回当前用户能看到的最新10条请假申请
class LatestAbsentView(APIView):
    #@method_decorator(cache_page(30))#缓存设置为30秒
    def get(self, request):
        # 董事会的人，可以看到所有人的考勤信息，非董事会的人，只能看到自己部门的考勤信息
        current_user = request.user
        queryset = Absent.objects
        if current_user.department.name != '董事会':
            queryset = queryset.filter(requester__department_id=current_user.department_id)
        queryset = queryset.all()[:10]
        serializer = AbsentSerializer(queryset, many=True)
        return Response(serializer.data)



#返回每个部门的员工数量
class DepartmentStaffCountView(APIView):
    #@method_decorator(cache_page(30))#缓存设置为30秒
    def get(self, request):
        rows = OAdepartment.objects.annotate(staff_count=Count("staffs")).values("name", "staff_count")
        # 执行步骤：
        # annotate(staff_count=Count("staffs"))
        # 在每个部门记录上添加一个临时的聚合字段 staff_count
        # "staffs"是OAdepartment模型定义的related_name（来自staff应用的ForeignKey反向引用）
        # SQL等价：GROUP BY department_id, COUNT(staffs.uid) AS staff_count
        # values("name", "staff_count")
        # 只返回两列：部门名称和员工数量
        # 返回结果是字典列表，不是模型对象
        # SQL等价：SELECT
        # department.name, staff_count FROM department
        # print(rows)
        print('='*10)
        return Response(rows)

#健康检查
class HealthCheckView(APIView):
    def get(self, request):
        return Response({"code": 200})


# HTTP Request（如 GET /api/home/latest-informs/）
#     ↓
# Django URL路由 → 匹配到对应的APIView
#     ↓
# APIView.get(request) 方法执行
#     ↓
# 【步骤1】获取当前用户：request.user（由认证中间件设置）
#     ↓
# 【步骤2】构建ORM查询
#     ├─ 定义QuerySet (对应SQL的SELECT...WHERE)
#     ├─ 应用Prefetch (预加载关联数据，避免N+1)
#     ├─ 应用filter/exclude (WHERE条件)
#     ├─ 应用[:10] (LIMIT 10)
#     ↓
# 【步骤3】执行查询（执行SQL）
#     ↓
# 【步骤4】序列化：Serializer将Model对象转为dict
#     ↓
# 【步骤5】返回Response（自动转为JSON）
#     ↓
# HTTP Response（JSON格式）