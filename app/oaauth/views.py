from django.shortcuts import render
from rest_framework.views import APIView
from .authentications import generate_jwt
from .serializer import LoginSerializer, UserSerializer, ResetPwdSerializer
from datetime import datetime
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated



#登录视图
class Login(APIView):
    def post(self, request):
        #1.验证数据是否可用
        serializer = LoginSerializer(data=request.data)#传入请求数据
        if serializer.is_valid():
            user=serializer.validated_data['user']#获取验证后的用户对象，来自serializer中attrs['user']
            #记录登录时间
            user.last_login=datetime.now()#更新最后登录时间为当前时间
            user.save()#保存用户对象
            token=generate_jwt(user)#生成JWT token
            return Response({'token':token,'user':UserSerializer(user).data})#返回token给客户端
        else:
            #{比如：person={"username":张三,"age"：18}
            #那么person.values()=[“张三”、18] 类型为dict_list也即字典列表
            detail=list(serializer.errors.values())[0][0]  #从dict_list转为list
            #drf在返回响应是非200时，错误参数名是detail，这里我们让他保持一致，这是为了前端处理方便，否则你传进去一个不叫detail的参数，axios会懵逼
            return Response({'detail':detail},status=status.HTTP_400_BAD_REQUEST)


class ResetPwdView(APIView):
    def post(self, request):
        # request: 是DRF封装的，rest_framework.request.Request
        # 这个对象是针对django的HttpRequest对象进行了封装

        serializer = ResetPwdSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            pwd1 = serializer.validated_data.get('pwd1')

            # 设置新密码并保存用户
            request.user.set_password(pwd1)
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

            # 注意：HTTP状态码应该是400，不是460
            return Response(
                data={"detail": detail},
                status=status.HTTP_400_BAD_REQUEST
            )







