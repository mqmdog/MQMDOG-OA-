from rest_framework import serializers  # 导入序列化器模块
from .models import OAUser, UserStatusChoices, OAdepartment
from rest_framework import exceptions  # 导入异常模块

# Serializer (DRF基类)
#     │
#     ├── Serializer (普通序列化器)
#     │       │
#     │       └── LoginSerializer  (自定义)
#     │
#     └── ModelSerializer (模型序列化器)
#             │
#             └── UserSerializer, DepartmentSerializer

class LoginSerializer(serializers.Serializer):  
    email = serializers.EmailField(required=True, error_messages={"required": "请输入邮箱！"})  # 邮箱字段，必填，错误信息自定义
    password = serializers.CharField(max_length=20, min_length=4)  # 密码字段，最大长度20，最小长度4

    def validate(self, attrs):  # 验证数据的方法,attrs为传入的数据字典
        email = attrs.get('email')  # 获取邮箱,attrs是传入的数据字典
        password = attrs.get('password')  # 获取密码

        if email and password:  # 如果邮箱和密码都存在
            user = OAUser.objects.filter(email=email).first()  # 根据邮箱查询用户，如果存在则返回第一个用户对象，否则返回None
            #等价于 SELECT * FROM oaauth_oauser WHERE email = 'xxx@qq.com' LIMIT 1;
            if not user:  # 如果用户不存在
                raise serializers.ValidationError("用户不存在")  # 抛出验证错误异常
            if not user.check_password(password):  # 如果密码不正确
                raise serializers.ValidationError("密码错误")  # 抛出验证错误异常
            # 判断状态
            if user.status == UserStatusChoices.UNACTIVE:
                raise serializers.ValidationError("用户未激活，请联系管理员")  # 抛出验证错误异常
            elif user.status == UserStatusChoices.LOCKED:
                raise serializers.ValidationError("用户已锁定，请联系管理员")  # 抛出验证错误异常
            # 为了节省执行sql语句的次数，这里我们直接把user对象放到attrs中，后续视图函数中可以直接使用
            attrs['user'] = user  # 将用户对象添加到attrs
        else:
            raise serializers.ValidationError("必须提供邮箱和密码进行登录")  # 抛出验证错误异常
        return attrs  # 返回验证后的数据


class DepartmentSerializer(serializers.ModelSerializer):#自动将OAdepartment模型转换为JSON
    class Meta:  #告诉序列化器使用哪个模型、包含哪些字段
        model = OAdepartment  # 指定序列化器对应的模型类
        fields = "__all__"  # 指定要序列化的字段为所有字段
        
        # # 方式1：所有字段
        # fields = "__all__"
        # 
        # # 方式2：指定字段列表
        # fields = ["id", "name", "intro"]
        # 
        # # 方式3：排除字段
        # exclude = ["id", "create_time"]
        


class UserSerializer(serializers.ModelSerializer): 
    department = DepartmentSerializer()  # 嵌套部门序列化器，在用户数据中包含部门详细信息

    class Meta:  # 元类，定义序列化器的元信息
        model = OAUser  # 指定序列化器对应的模型类
        exclude = ['password', 'groups', 'user_permissions']  # 排除密码、用户组（内置的）和用户权限（内置的）字段


class ResetPwdSerializer(serializers.Serializer):
    oldpwd = serializers.CharField(min_length=6, max_length=20)
    pwd1 = serializers.CharField(min_length=6, max_length=20)
    pwd2 = serializers.CharField(min_length=6, max_length=20)

    def validate(self, attrs):
        oldpwd = attrs['oldpwd']
        pwd1 = attrs['pwd1']
        pwd2 = attrs['pwd2']

        # ┌─────────────────────────────────────────────────────────────────┐
        # │                    context
        # 传递流程                              
        # │                                                                 
        # │  视图中：                                                       
        # │  ┌─────────────────────────────────────────────────────────┐   
        # │  │ serializer = ResetPwdSerializer(                        
        # │  │     data = request.data,                                    
        # │  │     context = {'request': request}  ← 传递context        
        # │  │ )                                                           
        # │  └─────────────────────────────────────────────────────────┘   
        # │                           ↓                                     
        # │  序列化器中：                                                   
        # │  ┌─────────────────────────────────────────────────────────┐   
        # │  │ user = self.context['request'].user  ← 获取当前用户       
        # │  └─────────────────────────────────────────────────────────┘   
        # │                                                                 │
        # └─────────────────────────────────────────────────────────────────┘

        # 从上下文中获取当前用户
        user = self.context['request'].user

        # 验证旧密码是否正确
        if not user.check_password(oldpwd):
            raise exceptions.ValidationError("旧密码错误！")

        # 验证两个新密码是否一致
        if pwd1 != pwd2:
            raise exceptions.ValidationError("两个新密码不一致！")

        return attrs
