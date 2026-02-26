from rest_framework import viewsets
from rest_framework import mixins   #mixins翻译成中文是混入，组件的意思。在DRF中，针对获取列表，检索，创建等操作，都有相应的mixin
from rest_framework.response import Response #响应对象
from .models import Absent, AbsentType #导入模型
from .serializer import AbsentSerializer,AbsentTypeSerializer #导入序列化器
from rest_framework.views import APIView #API视图
from .utils import get_responder #获取审批者
from app.oaauth.serializer import UserSerializer #用户序列化器


# # 视图集（ViewSet）是REST framework提供的一个概念，它将多个相关操作组合在一起，提供一种更简洁的方式来处理URL路由。
# # rest_framework/viewsets.py
# __all__ = ['ViewSet', 'GenericViewSet', 'ModelViewSet', 'ReadOnlyModelViewSet']
#
# # ViewSet: 基本视图集
# # GenericViewSet: 通用视图集（可定制混入）
# # ModelViewSet: 模型视图集（完整CRUD）
# # ReadOnlyModelViewSet: 只读模型视图集

# View (Django)
#     │
# APIView (DRF)
#     │
# GenericAPIView (DRF)  ──→ 提供queryset、serializer_class等通用属性
#     │
# ViewSet (DRF)  ──────→ 继承GenericAPIView + ViewSetMixin
#     │
# GenericViewSet (DRF) ──→ 继承GenericAPIView + ViewSetMixin（无默认操作）
#     │
# ModelViewSet ──────────→ 继承GenericViewSet + 各种Mixin（完整CRUD）


# # 继承多个Mixin，获得组合功能
# class MyViewSet(CreateModelMixin, ListModelMixin, GenericViewSet):
#     pass
#
# # MyViewSet 获得的方法：
# # - create() 来自 CreateModelMixin
# # - list()   来自 ListModelMixin
# # - get_queryset() 来自 GenericViewSet
# # - get_serializer() 来自 GenericViewSet


# ┌─────────────────────────────────────────────────────────────────┐
# │                       视图职责图                                   │
# │                                                                 │
# │   AbsentViewSet              → 请假记录的增删改查                │
# │          ├── create()         → 发起请假                         │
# │          ├── update()         → 处理请假（审批）                 │
# │          ├── list()           → 查看请假列表（自己/下属）        │
# │                                                                 │
# │   AbsentTypeView             → 请假类型列表                      │
# │          └── get()            → 获取所有请假类型                 │
# │                                                                 │
# │   ResponderView              → 审批人信息                         │
# │          └── get()            → 获取当前用户的审批人              │
# │                                                                 │
# └─────────────────────────────────────────────────────────────────┘


class AbsentViewSet(
    mixins.CreateModelMixin, #创建
    mixins.UpdateModelMixin, #更新
    mixins.ListModelMixin,   #列表
    viewsets.GenericViewSet #通用视图集
): #通过组合不同的Mixin，获取需要的CRUD功能

    # queryset 是懒执行的，不会立即查询数据库，而是在需要时才查询
    queryset = Absent.objects.all()# queryset是查询集，即所有数据的集合，这里表示获取所有考勤数据，SELECT * FROM absent_absent

    serializer_class = AbsentSerializer # 告诉DRF使用哪个序列化器来转换数据

    #重写update方法，这一段代码表示重写update方法，使得可以只修改部分数据
    def update(self, request, *args, **kwargs):
        #默认情况下，如果想修改某一条数据，那么要把这个数据的序列化中指定的字段都上传
        #如果想只修改一部分数据，那么可以在kwargs中设置partial=True
        kwargs['partial'] = True#告诉DRF只修改部分数据，将PUT请求转换为PATCH请求，支持部分更新
        return super().update(request, *args, **kwargs)#继续执行update方法

    # # 本项目的业务场景：审批请假
    # # 审批时只需要修改状态字段，不需要提交全部字段
    # # 不重写的情况：
    # PUT / absent / absent / 1
    # {
    #     "status": 2  # 只传了status
    # }
    # # 结果：其他字段会被清空！
    #
    # # 重写后：
    # PATCH / absent / absent / 1  # 实际调用时使用PUT
    # {
    #     "status": 2  # 只传了status
    # # 结果：只修改status，其他字段不变

    #重写list方法，这一段代码表示重写list方法，使得可以按who参数查询下属或自己的考勤
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()#获取所有考勤数据，和queryset = Absent.objects.all()等价
        who=request.query_params.get('who') #获取who参数，用于查询下属或自己的考勤 # query_params是Django REST Framework对Django request.GET的封装
        # get()方法安全地获取参数，如果参数不存在则返回None
        if who and who=='sub':#检查who参数是否存在且值是否为'sub'
            result=queryset.filter(responder=request.user)#查询下属的考勤
        else:
            result=queryset.filter(requester=request.user)#查询自己的考勤
        #result代表符合要求的数据

        # ┌─────────────────────────────────────────────────────────────────┐
        # │                        分页处理流程                               │
        # │                                                                 │
        # │  1.
        # 请求到达
        # │     GET / absent / absent?page = 1 & page_size = 10
        # │
        # │  2.
        # paginate_queryset()
        # │     ├── 检查是否配置了分页
        # │     ├── 对查询集进行切片：result[0:10]
        # │     ├── 返回分页后的数据
        # page
        # │     └── 如果没有分页配置，返回
        # None
        # │
        # │  3.
        # 序列化
        # │     get_serializer(page, many=True)
        # │     ├── many = True
        # 表示序列化多个对象
        # │     └── 返回序列化后的数据
        # │
        # │  4.
        # 返回响应
        # │     get_paginated_response(serializer.data)
        # │     ├── 返回数据 + 分页信息
        # │     └── 格式：{
        # │            "count": 100,  # 总数
        # │            "next": "...",  # 下一页URL
        # │            "previous": "...",  # 上一页URL
        # │            "results": [...]  # 数据列表
        # │}
        # │                                                                 │
        # └─────────────────────────────────────────────────────────────────┘


        #pageinage_queryset方法：会做分页的逻辑处理
        page=self.paginate_queryset(result)
        #此时page的结构是：{'count': 1, 'next': None, 'previous': None, 'results': [{'id': 1, 'name': '张三', 'age': 18}]}
        #如果page不为空，则返回分页后的数据
        if page is not None:
            serializer=self.get_serializer(page,many=True) #序列化分页后的数据，many=True表示要序列化的是查询集（多个对象），而不是单个对象
            return self.get_paginated_response(serializer.data)#get_paginated_response:除了返回序列化后的数据外，还会返回总数据多少，上一页url是什么
        #此时serializer.data的结构是：{'count': 1, 'next': None, 'previous': None, 'results': [{'id': 1, 'name': '张三', 'age': 18}]}
        #如果page为空，则返回所有数据
        serializer=self.serializer_class(result,many=True) #序列化所有数据，many=True表示要序列化的是查询集（多个对象），而不是单个对象

        return Response(serializer.data) #返回序列化后的数据

    # 返回考勤类型列表
class AbsentTypeView(APIView):
    def get(self,request):
        queryset=AbsentType.objects.all() # 获取所有考勤类型数据
        serializer=AbsentTypeSerializer(queryset,many=True) # 序列化所有考勤类型数据，many=True表示要序列化的是查询集（多个对象），而不是单个对象
        return Response(data=serializer.data) # 返回序列化后的数据

#显示审批者
class ResponderView(APIView):
    def get(self,request):
        responder=get_responder(request)
        #Serializer:如果序列化的对象是一个None，那么不会报错，而是返回一个包含除了主键之外的所有字段的空字典
        serializer=UserSerializer(responder)
        return Response(data=serializer.data)




