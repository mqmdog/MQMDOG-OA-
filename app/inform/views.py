from rest_framework import viewsets
from .models import Inform, InformRead
from .serializer import InformSerializer,ReadInformSerializer
from django.db.models import Q # 用于多个条件的并查
from rest_framework.response import Response 
from rest_framework import status # HTTP状态码
from rest_framework.views import APIView # API视图
from django.db.models import Prefetch # 预查询优化


class InformViewSet(viewsets.ModelViewSet):  # 提供完整的 CRUD 接口（列表、详情、创建、更新、删除）。
    queryset = Inform.objects.all()  # 获取所有通知
    serializer_class = InformSerializer  # 序列化器

    # 重写get_queryset方法，实现通知列表的过滤
    def get_queryset(self): 
        # 如果多个条件的并查，那么就需要用到Q函数
        queryset = self.queryset.select_related('author').prefetch_related(Prefetch("reads", queryset=InformRead.objects.filter(user_id=self.request.user.uid)), 'departments').filter(Q(public=True) | Q(departments=self.request.user.department) | Q(author=self.request.user)).distinct()
        #逻辑分析：
        #使用 Q 对象实现 OR 逻辑（ | 表示 OR），三种条件满足其一即可显示。
        # public = True	公开通知（所有人可见）
        # departments = 用户部门	发送给特定部门的通知
        # author = 当前用户	用户自己创建的通知
        
        # 性能优化：
        #select_related('author') - 预加载作者信息（避免 N+1 查询）
        #prefetch_related('departments') - 预加载部门信息
        #Prefetch("reads", ...) - 自定义预加载已读记录，只加载当前用户已读状态
        # distinct() - 去重

        return queryset
        # for inform in queryset:
        #     inform.is_read = InformRead.objects.filter(inform=inform, user=self.request.user).exsits()
        # return queryset

    # 重写检索方法，实现通知详情的扩展，返回通知详情时，额外添加已读人数 read_count。
    def retrieve(self, request, *args, **kwargs):
            instance = self.get_object() # 获取通知实例
            serializer = self.get_serializer(instance) # 获取序列化器
            data=serializer.data # 获取序列化数据
            data['read_count']=InformRead.objects.filter(inform_id=instance.id).count() # 获取已读记录数
            return Response(data=data) # 返回数据

    # 只有通知的创建者才能删除自己的通知，其他用户无权限删除
    def destroy(self, request, *args, **kwargs):# 删除通知
        instance = self.get_object() # 获取通知实例
        if instance.author.uid == request.user.uid: # 判断当前用户是否是通知的创建者
            self.perform_destroy(instance) # 删除通知实例
            return Response(status=status.HTTP_204_NO_CONTENT) # 返回204状态码
        else:
            return Response(status=status.HTTP_401_FORBIDDEN) # 返回401状态码

# 用于用户标记通知为已读，已读则直接返回，未读则创建已读记录
class ReadInformView(APIView):
    def post(self, request):
        # 通知的id
        serializer = ReadInformSerializer(data=request.data)
        if serializer.is_valid():
            inform_pk = serializer.validated_data.get('inform_pk') # 获取通知的id
            # 判断当前用户是否已读过该通知
            if InformRead.objects.filter(inform_id=inform_pk, user_id=request.user.uid).exists():
                return Response() #已读则直接返回
            else:
                try:
                    # 创建已读记录
                    InformRead.objects.create(inform_id=inform_pk, user_id=request.user.uid)
                except Exception as e:
                    print(e)
                    return Response(status=status.HTTP_400_BAD_REQUEST)
                return Response()
        else:
            return Response(data={'detail': list(serializer.errors.values())[0][0]}, status=status.HTTP_400_BAD_REQUEST)