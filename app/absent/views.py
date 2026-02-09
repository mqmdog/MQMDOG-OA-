#Django视图（View）是连接模型（Model）和模板（Template）的核心组件，负责处理HTTP请求并返回HTTP响应。它是Django MTV（Model-Template-View）架构中的控制器。
from django.shortcuts import render
from rest_framework import viewsets #ViewSet视图集，相当于是之前我们学习视图的一个集合。在视图集中，不再有get和post，取而代之的是list和create
from rest_framework import mixins   #mixins翻译成中文是混入，组件的意思。在DRF中，针对获取列表，检索，创建等操作，都有相应的mixin
from rest_framework.response import Response #响应对象
from .models import Absent, AbsentType #导入模型
from .serializer import AbsentSerializer,AbsentTypeSerializer #导入序列化器
from rest_framework.views import APIView #API视图
from .utils import get_responder #获取审批者
from app.oaauth.serializer import UserSerializer #用户序列化器

#1.发起考勤create
#2.处理考勤update

#3.查看自己的考勤列表list?who=xxx
#4.查看下属的考勤列表list?who=sub


class AbsentViewSet(
    mixins.CreateModelMixin, #创建
    mixins.UpdateModelMixin, #更新
    mixins.ListModelMixin,   #列表
    viewsets.GenericViewSet #通用视图集
): #继承自mixins，viewsets

    queryset = Absent.objects.all()   # queryset是查询集，即所有数据的集合，这里表示获取所有考勤数据

    serializer_class = AbsentSerializer # 告诉DRF使用哪个序列化器来转换数据

    #重写update方法，这一段代码表示重写update方法，使得可以只修改部分数据
    def update(self, request, *args, **kwargs):
        #默认情况下，如果想修改某一条数据，那么要把这个数据的序列化中指定的字段都上传
        #如果想只修改一部分数据，那么可以在kwargs中设置partial=True
        kwargs['partial'] = True#告诉DRF只修改部分数据
        return super().update(request, *args, **kwargs)#继续执行update方法

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




