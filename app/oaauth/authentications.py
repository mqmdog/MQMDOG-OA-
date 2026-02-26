import jwt#导入PyJWT库
import time#导入时间模块
from django.conf import settings#导入Django的设置模块
from rest_framework.authentication import BaseAuthentication,get_authorization_header#导入DRF的认证基类和获取授权头函数
from rest_framework import exceptions#导入DRF的异常模块
from jwt.exceptions import ExpiredSignatureError#导入JWT的过期签名异常
from .models import OAUser#导入自定义用户模型

def generate_jwt(user):#生成JWT token
    expire_time = time.time() + 60*60*24*7#设置过期时间为7天
    return jwt.encode({"userid":user.pk,"exp":expire_time},key=settings.SECRET_KEY)#使用Django的SECRET_KEY进行加密
    #参数为payload，key，algorithm



class UserTokenAuthentication(BaseAuthentication): #
    """这是一个桥接类，用于在某些特定场景下将Django的原生认证转换为DRF格式。"""
    def authenticate(self, request):
        return request._request.user,request._request.auth
    #DRF的 request 是 rest_framework.request.Request 类
    # Django原生的是 django.http.HttpRequest 类
    # DRF在内部保存了原生request：request._request


class JWTAuthentication(BaseAuthentication):#JWT认证类，继承自DRF的BaseAuthentication

    keyword = 'JWT'#定义认证头的关键字


    def authenticate(self, request):#认证方法
        auth = get_authorization_header(request).split()#获取请求头中的授权信息并拆分
        # 假设请求头
        # Authorization: JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        # get_authorization_header(request)
        # 返回: b'JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

        # .split()
        # 返回: [b'JWT', b'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9

        if not auth or auth[0].lower() != self.keyword.lower().encode(): #b'jwt' != b'jwt'
            #检查授权头是否存在且以指定关键字开头
            return None

        if len(auth) == 1:#检查授权头格式是否正确
            msg = 'Authorization不可用！'
            raise exceptions.AuthenticationFailed(msg)#抛出认证失败异常
        elif len(auth) > 2:#检查授权头格式是否正确
            msg = 'Authorization不可用！应该提供一个空格！'
            raise exceptions.AuthenticationFailed(msg)

        try:#尝试解码JWT token
            jwt_token = auth[1]#获取token部分
            jwt_info = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms="HS256")#解码token
            userid = jwt_info.get('userid')#获取用户ID
            try:
                #绑定当前user到request对象上
                user = OAUser.objects.get(pk=userid)#根据用户ID获取用户对象
                setattr(request, 'user', user)#将用户对象绑定到请求对象上，语法为setattr(object, name, value)，其中object是要设置属性的对象，name是属性名，value是属性值
                #等价于request.uer=user
                return user, jwt_token#返回用户对象和token
            except Exception:
                msg = '用户不存在！'#用户不存在异常处理
                raise exceptions.AuthenticationFailed(msg)#抛出认证失败异常
        except ExpiredSignatureError:
            msg = "JWT Token已过期！"
            raise exceptions.AuthenticationFailed(msg)