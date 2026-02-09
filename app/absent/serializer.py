from rest_framework import serializers # 导入序列化器模块
from .models import Absent, AbsentType, AbsentStatusChoices # 导入模型类
from app.oaauth.serializer import UserSerializer # 导入用户序列化器
from rest_framework import exceptions # 导入异常类
from .utils import get_responder # 导入获取审批人函数


class AbsentTypeSerializer(serializers.ModelSerializer): # 定义一个考勤类型序列化器
    class Meta:
        model = AbsentType# 指定模型类为AbsentType
        fields = "__all__"# 指定所有字段都序列化


class AbsentSerializer(serializers.ModelSerializer):
    #1. read_only=True：这个字段只只能读，只有在返回数据的时候会使用。
    #2. write_only=True：这个字段只能被写，只有在新增数据或者更新数据的时候会用到

    absent_type = AbsentTypeSerializer(read_only=True)#read_only=True: 只读，即在序列化时包含这个字段，在反序列化时忽略这个字段
    absent_type_id = serializers.IntegerField(write_only=True)#write_only=True: 只写，即在反序列化时包含这个字段，在序列化时忽略这个字段
    #这样做是为了在序列化时，将absent_type_id转换为absent_type
    requester = UserSerializer(read_only=True)#read_only=True: 只读，即在序列化时包含这个字段，在反序列化时忽略这个字段
    responder = UserSerializer(read_only=True)#read_only=True: 只读，即在序列化时包含这个字段，在反序列化时忽略这个字段

    class Meta:
        model = Absent# 指定模型类为Absent
        fields = "__all__"# 指定所有字段都序列化

    # 验证absent_type_id是否在数据库中存在
    def validate_absent_type_id(self, value):
        if not AbsentType.objects.filter(pk=value).exists(): # pk=value: 通过主键查找，value是用户传入的ID
            raise exceptions.ValidationError("考勤类型不存在！")
        return value

    # create方法 - 用于创建新的请假审批记录
    def create(self, validated_data): #validated_data: 经过序列化器验证后的数据字典，相当于上面初步序列化后的数据字典
        request = self.context['request']  # 获取请求对象
        """
        context是Django REST Framework中用于传递额外信息的参数，它包含：
        - request: 当前的HTTP请求对象，包含请求的详细信息，如用户信息、请求头、请求体等
                   请求体中包含用户信息，如用户ID、用户名、权限等
                   请求头中包含CSRF令牌等信息，请求方法（GET、POST等）等信息
        - view: 当前的视图对象，包含当前请求的处理逻辑
        - args: 当前视图的参数列表
        - kwargs: 当前视图的关键字参数列表  
        - other: 其他可能需要的参数
        """
        user = request.user  # 获取当前用户
        responder=get_responder(request)#通过请求对象获取审批人
        """
        get_responder函数会返回一个用户对象，这个用户对象就是审批人
        """
        if responder is None:
            validated_data['status'] = AbsentStatusChoices.PASS #如果是董事会的leader，审批直接通过
        else:
            validated_data['status']=AbsentStatusChoices.AUDITING #如果是部门leader，审批状态为审核中

        # 调用模型类的create方法，创建新的请假审批记录，包含请求对象和审批人，**validated_data 包含已经通过序列化器验证的所有字段数据
        absent=Absent.objects.create(**validated_data,requester=user,responder=responder)
        #absent包含字段有：id, absent_type, absent_type_id, requester, responder, start_time, end_time, reason, status, response_content, created_at, updated_at

        return absent


    # update方法 - 用于更新请假审批记录，判断是否有更新审批的权限，并修改状态和审批内容，保存在数据库中，然后返回更新后的实例
    def update(self, instance, validated_data):
        """
        参数说明：
        - instance: 当前要更新的Absent模型实例（数据库中的原请假记录）
        - validated_data: 经过序列化器验证后的数据字典
        """

        # 检查请假记录当前状态
        # 只有处于"审核中"状态的记录才能被修改
        if instance.status != AbsentStatusChoices.AUDITING:
            # 如果状态不是AUDITING（审核中）
            # 比如可能是已批准、已拒绝、已撤销等状态
            raise exceptions.APIException(detail='不能修改已经确定的请假数据！')
            # 抛出API异常，阻止继续执行
            # detail参数是返回给客户端的错误信息

        # 获取当前HTTP请求对象
        # DRF序列化器的context中包含了request信息
        request = self.context['request']

        # 从请求中获取当前登录用户
        user = request.user

        # 权限验证：检查当前用户是否为该请假记录的负责人
        # 只有请假记录的负责人才能进行审批操作
        if instance.responder.uid != user.uid:  # 如果请假记录中的负责人UID与当前用户UID不匹配
            raise exceptions.AuthenticationFailed(detail='您无权处理该考勤！')
            # 抛出认证失败异常，表示用户无权限
            # 注意：这里用的是AuthenticationFailed，但实际上是权限问题
            # 更合适的可能是PermissionDenied异常

        # 更新请假记录的状态
        # validated_data['status'] 是用户提交的新状态
        # 可能是批准、拒绝等状态
        instance.status = validated_data['status']

        # 更新审批内容/备注
        # validated_data['response_content'] 是审批意见或说明
        instance.response_content = validated_data['response_content']

        # 将更新保存到数据库
        instance.save()

        # 返回更新后的实例
        return instance

