#全局登录检查中间件，用于在每个请求到达视图之前验证用户的登录状态：
from django.contrib.auth.models import AnonymousUser # 匿名用户类，用于表示未认证的用户
from django.http import JsonResponse #返回JSON格式的Http响应
from django.utils.deprecation import MiddlewareMixin
from rest_framework.authentication import get_authorization_header
from rest_framework import exceptions
from jwt import ExpiredSignatureError # JWT过期错误类
import jwt # JSON Web Token库
from django.conf import settings # Django设置模块
from django.contrib.auth import get_user_model # 获取用户模型
from rest_framework.status import HTTP_403_FORBIDDEN # HTTP 403状态码
from django.shortcuts import reverse # 反向解析URL
# ┌─────────────────────────────────────────────────────────────────┐
# │                       中间件职责                                  │
# │                                                                 │
# │   客户端请求 ──→ 中间件检查Token ──→ 验证通过 ──→ 视图处理     │
# │                      ↓                                          │
# │                 白名单路径 ──→ 直接放行 ──→ 视图处理           │
# │                      ↓                                          │
# │                 Token无效 ──→ 返回403 ──→ 请求结束             │
# │                                                                 │
# └─────────────────────────────────────────────────────────────────┘


# 获取用户模型，这里重命名为 OAUser
OAUser = get_user_model()


class LoginCheckMiddleware(MiddlewareMixin):
    """登录检查中间件，继承MiddlewareMixin实现兼容性"""
    # JWT 令牌前缀，用于识别授权头的类型
    keyword = 'JWT'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.white_list=[reverse("oaauth:login"),reverse("staff:active_staff")] # 白名单路径列表，用于存放不需要登录检查的路径

    def process_view(self,request,view_func,view_args,view_kwargs): # 视图函数执行之前进行拦截处
        # 如果是白名单路径，则不进行登录检查;路径是媒体文件，放行
        if request.path in self.white_list or request.path.startswith('/api'+ settings.MEDIA_URL):
            request.user = AnonymousUser() #设置为匿名用户
            request.auth = None #无认证信息
            return None #返回None，继续执行视图
        try:
            auth = get_authorization_header(request).split()  # 获取请求头中的授权信息并拆分

            if not auth or auth[0].lower() != self.keyword.lower().encode():  # 检查授权头是否存在且以指定关键字开头
                raise exceptions.ValidationError('请传入JWT!')# 抛出认证失败异常

            if len(auth) == 1:  # 检查授权头格式是否正确
                msg = 'Authorization不可用！'
                raise exceptions.AuthenticationFailed(msg)  # 抛出认证失败异常
            elif len(auth) > 2:  # 检查授权头格式是否正确
                msg = 'Authorization不可用！应该提供一个空格！'
                raise exceptions.AuthenticationFailed(msg)

            try:  # 尝试解码JWT token
                jwt_token = auth[1]  # 获取token部分
                jwt_info = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms="HS256")  # 解码token
                userid = jwt_info.get('userid')  # 获取用户ID
                try:
                    # 绑定当前user到request对象上
                    user = OAUser.objects.get(pk=userid)  # 根据用户ID获取用户对象
                    setattr(request, 'user', user)  # 将用户对象绑定到请求对象上，语法为setattr(object, name, value)，其中object是要设置属性的对象，name是属性名，value是属性值
                    request.user= user
                    request.auth= jwt_token
                except Exception:
                    msg = '用户不存在！'  # 用户不存在异常处理
                    raise exceptions.AuthenticationFailed(msg)  # 抛出认证失败异常
            except ExpiredSignatureError:
                msg = "JWT Token已过期！"
                raise exceptions.AuthenticationFailed(msg)
        except Exception as e:
            print(e)
            return JsonResponse({'message': '请先登录！'}, status=HTTP_403_FORBIDDEN)