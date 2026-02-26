from django.shortcuts import render
from rest_framework.views import APIView #类视图，提供RESTful API的请求处理能力，集成认证、权限、序列化器等DRF核心组件
from .authentications import generate_jwt #生成JWT token，JSON Web Token
from .serializer import LoginSerializer, UserSerializer, ResetPwdSerializer #序列化器，将数据在不同表示之间进行转换
from datetime import datetime #时间，处理日期和时间相关的操作
from rest_framework.response import Response #响应，返回HTTP响应
from rest_framework import status #状态码，HTTP状态码的常量
from rest_framework.permissions import IsAuthenticated #权限，权限控制

# 常见变体： | 类 | 特点 | 适用场景 |
# |---|---|---|
# | APIView | 基础视图，最灵活 | 复杂业务逻辑 |
# | GenericAPIView | 增加查询集、序列化器支持 | 标准的CRUD |
# | ListCreateAPIView | 继承GenericAPIView + ListModelMixin + CreateModelMixin | 列表+创建 |
# | ViewSet | 可映射多个动作 | 资源管理 |

# 客户端 POST /api/login
#     ↓
# {
#     "email": "user@example.com",
#     "password": "123456"
# }
#     ↓
# LoginSerializer 验证:
#     ↓
#     ├── 检查字段存在性
#     ├── validate() 验证:
#     │   ├── 根据email查询用户
#     │   ├── 验证密码 (user.check_password)
#     │   ├── 检查用户状态 (UNACTIVE/LOCKED)
#     │   └── 将user对象放入attrs['user']
#     ↓
# 验证通过
#     ↓
# ① 更新最后登录时间: user.last_login = datetime.now()
# ② 生成JWT令牌: token = generate_jwt(user)
# ③ 返回响应: {token, user信息}


#登录接口
class Login(APIView):
    def post(self, request):
        # request: 是DRF封装的，rest_framework.request.Request 对象，对Django原生的 HttpRequest 进行了扩展。
        # 统一处理不同前端提交的数据格式（JSON、表单、文件等）
        # 提供.data属性获取请求体数据
        # 提供.query_params获取URL查询参数，获取查询参数
        # 提供.user获取当前认证用户，获取当前用户

        # ❌ 错误：使用Django原生request.POST
        #user = request.POST.get('email')  # JSON请求体中无数据

        # ✅ 正确：使用DRF的request.data
        #user = request.data.get('email')  # 自动解析JSON

        #1.验证数据是否可用
        serializer = LoginSerializer(data=request.data)#传入请求数据
        #序列化器是DRF的核心组件，位于视图层与模型层之间。
        # 作用目的：
        # 数据验证：检查前端传入的数据是否合法
        # 数据转换：将模型对象转换为JSON（序列化） / 将JSON转换为模型对象（反序列化）
        # 关联对象处理：处理外键、多对多等复杂关系

        if serializer.is_valid(): #触发序列化器内部的所有验证逻辑
            # request.data
            # ↓
            # LoginSerializer.data = request.data
            # ↓
            # is_valid()
            # 执行:
            # ↓
            # ├── 字段级验证(EmailField, CharField)
            # ├── 全局验证(validate方法)
            # └── 抛出ValidationError或返回True
            # ↓
            # serializer.validated_data  # 验证通过后的干净数据
            user=serializer.validated_data['user']#获取验证后的用户对象，来自serializer中attrs['user']
            # 前端POST请求
            # ↓
            # request.data = {"email": "xxx@qq.com", "password": "1234"}
            # ↓
            # LoginSerializer(data=request.data)
            # ↓
            # is_valid()
            # 执行
            # validate()
            # 方法
            # ↓
            # attrs['user'] = user_object  # 在validate中手动添加
            # ↓
            # serializer.validated_data = {"email": "xxx@qq.com", "password": "1234", "user": < OAUser对象 >}

            #记录登录时间
            user.last_login=datetime.now()#更新最后登录时间为当前时间
            user.save()#保存用户对象
            #Django的ORM在调用.save()时，会执行UPDATE语句更新数据库中的last_login字段。

            token=generate_jwt(user)#生成JWT token
            return Response({'token':token,'user':UserSerializer(user).data})#返回token给客户端，自动将Python字典转换为JSON响应
        else:
            #{比如：person={"username":张三,"age"：18}
            #那么person.values()=[“张三”、18] 类型为dict_list也即字典列表
            detail=list(serializer.errors.values())[0][0]  #从dict_list转为list
            #drf在返回响应是非200时，错误参数名是detail，这里我们让他保持一致，这是为了前端处理方便，否则你传进去一个不叫detail的参数，axios会懵逼
            return Response({'detail':detail},status=status.HTTP_400_BAD_REQUEST)

# 客户端 POST /api/reset-password (需带JWT)
#     ↓
# Headers: Authorization: JWT xxxxx.yyyyy.zzzzz
#     ↓
# {
#     "oldpwd": "旧密码",
#     "pwd1": "新密码1",
#     "pwd2": "新密码2"
# }
#     ↓
# ResetPwdSerializer 验证:
#     ↓
#     ├── 检查字段长度 (6-20)
#     ├── validate() 验证:
#     │   ├── 从context获取当前用户: self.context['request'].user
#     │   ├── 验证旧密码: user.check_password(oldpwd)
#     │   └── 验证两次新密码一致: pwd1 == pwd2
#     ↓
# 验证通过
#     ↓
# request.user.set_password(pwd1)  # 加密新密码
# request.user.save()  # 保存到数据库
#     ↓
# 返回成功响应

#重置密码接口
class ResetPwdView(APIView):
    def post(self, request):
        serializer = ResetPwdSerializer(
            data=request.data,
            context={'request': request} # 传递当前请求对象,在序列化器中可以通过self.context['request'].user获取当前对象
        )

        if serializer.is_valid():
            pwd1 = serializer.validated_data.get('pwd1') # 获取验证通过后的新密码

            # 设置新密码并保存用户
            request.user.set_password(pwd1) #Django内置用户模型 AbstractBaseUser 提供的方法，会自动加密新密码
            request.user.save()

            return Response({
                'message': '密码修改成功',
                'status': 'success'
            }, status=status.HTTP_200_OK)
        else:
            # 打印错误信息用于调试
            print(serializer.errors)

            # 提取第一个错误信息
            detail = list(serializer.errors.values())[0][0]
            # # 1. .values() 取出所有值
            # dict_values([['用户不存在'], ['密码错误']])
            # # 2. 转为list
            # [['用户不存在'], ['密码错误']]
            # # 3. 取第一个元素 (第一个字段的错误列表)
            # ['用户不存在']
            # # 4. 取第一个错误信息
            # '用户不存在'

            # HTTP状态码应该是400
            return Response(
                data={"detail": detail},
                status=status.HTTP_400_BAD_REQUEST
            )


# ┌─────────────────────────────────────────────────────────────────┐
# │                         客户端请求                               │
# │   POST /api/login  {email, password}                           │
# └───────────────────────────┬─────────────────────────────────────┘
#                             │
#                             ▼
# ┌─────────────────────────────────────────────────────────────────┐
# │                    DRF 请求拦截                                  │
# │   request = rest_framework.request.Request                     │
# │   request.data = {email, password}                             │
# └───────────────────────────┬─────────────────────────────────────┘
#                             │
#                             ▼
# ┌─────────────────────────────────────────────────────────────────┐
# │                   LoginSerializer 验证                          │
# │   1. 字段验证 (EmailField, CharField)                          │
# │   2. validate() 自定义验证                                      │
# │      - 查询用户: OAUser.objects.filter(email=email).first()    │
# │      - 验证密码: user.check_password(password)                │
# │      - 检查状态: user.status                                    │
# └───────────────────────────┬─────────────────────────────────────┘
#                             │
#               ┌─────────────┴─────────────┐
#               │         验证结果            │
#               ▼                             ▼
#         验证通过                        验证失败
#               │                             │
#               ▼                             ▼
#     ┌─────────────────┐           ┌─────────────────┐
#     │ 1. 更新last_login│           │ 提取错误信息     │
#     │ 2. 生成JWT token │           │ Response 400   │
#     │ 3. 返回Response  │           └─────────────────┘
#     └─────────────────┘
#



