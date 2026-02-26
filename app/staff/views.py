from django.shortcuts import render
from rest_framework.generics import ListAPIView
from app.oaauth.models import OAdepartment,UserStatusChoices
from app.oaauth.serializer import DepartmentSerializer
from rest_framework.views import APIView
from .serializer import AddStaffSerializer,ActiveStaffSerializer,StaffUploadSerializer
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from utils import aeser
from django.urls import reverse
from OA_back.celery import debug_task
from .tasks import send_mail_task
from django.views import View
from django.http.response import JsonResponse
from urllib import parse
from rest_framework import generics
from rest_framework import exceptions
from app.oaauth.serializer import UserSerializer
from .paginations import StaffPagination
from rest_framework import viewsets
from rest_framework import mixins
from datetime import datetime
import json
import pandas as pd
from django.http import HttpResponse
from django.db import transaction

OAUser = get_user_model()
aes = aeser.AESCipher(settings.SECRET_KEY)  # 创建AES对象


def send_active_email(request, email):
    #1.加密邮件生成token
    token = aes.encrypt(email)

    # 2. 构造激活链接
    # /staff/active?token=xxx
    active_path = reverse('staff:active_staff') + '?' + parse.urlencode({'token': token})
    # http://127.0.0.1:8000/staff/active?token=xxx
    # http://127.0.0.1:8000/staff/active?token=RjgSom2/sCUNAIJ/I5/0p49X5hdLD5IpNq61vJ2kj9e1vBL/hmrURC2IH8nU+L0q
    active_url = request.build_absolute_uri(active_path)  # 完整URL
    # 发送一个链接，让用户点击这个链接后，跳转到激活的页面，才能激活
    # 为了区分用户，在发送链接的邮件中，该链接中应该要包含这个用户的邮箱
    # 针对邮箱要进行加密：AES
    message = f'请点击激活链接激活账号：{active_url}'
    subject = 'XHC-OA账号激活'
    # send_mail(f'XHC-OA账号激活', recipient_list=[email], message=message,from_email=settings.DEFAULT_FROM_EMAIL)
    send_mail_task.delay(email, subject, message)


# 返回所有部门列表（GET /api/departments）
class DepartmentListView(ListAPIView):
    queryset = OAdepartment.objects.all()
    serializer_class = DepartmentSerializer


#激活员工的过程
#1.用户访问激活的连接的时候，会返回一个含有表单的页面，视图中可以获取到token，为了在用户提交表单的时候，post函数中能知道这个token
#我们可以在返回页面之前，先把token存储在cookie中
#2.校验用户上传的邮箱和密码是否正确，并且解密token中的邮箱，与用户提交的邮箱进行对比，如果都相同，那么就是激活成功

# 激活员工
class ActiveStaffView(View):
    def get(self,request):
        #获取token，并且吧token存储在cookie中，方便下次用户传过来
        token = request.GET.get('token')
        response=render(request,'active.html')
        response.set_cookie('token', token)
        return response

    def post(self, request):
       #从cookie中获取token
        try:
            #  从 cookie 获取 token 并解密
            token = request.COOKIES.get('token')
            email = aes.decrypt(token)
            # 验证邮箱和密码
            serializer = ActiveStaffSerializer(data=request.POST)
            if serializer.is_valid():
                form_email = serializer.validated_data.get('email')
                user=serializer.validated_data.get('user')
                if email != form_email:
                    return JsonResponse({'code':400,'message':'邮箱错误！'})
                user.status = UserStatusChoices.ACTIVED
                user.save()
                return JsonResponse({'code':200,'message':'激活成功！'})
            else:
                detail=list(serializer.errors.values())[0][0]
                return JsonResponse({'code':400,'message':detail})


        except Exception as e:
            return JsonResponse({'code':400,'message':'token错误！'})


# 获取员工列表
class StaffView(generics.ListCreateAPIView):
    queryset=OAUser.objects.all()
    pagination_class = StaffPagination

    def get_serializer_class(self):
       if self.request.method=='GET':
           return UserSerializer
       else:
           return AddStaffSerializer
    def get_queryset(self):
        queryset = self.queryset
        #返回员工列表逻辑
        #1.如果是董事会的，那么返回所有员工
        #2.如果不是董事会的，但是是部门的leader，那么返回部门员工列表
        #3.一般员工，抛出403 Forbidden错误
        user=self.request.user
        if user.department.name != "董事会":
            if user.uid != user.department.leader.uid:
                raise exceptions.PermissionDenied()
            else:
                queryset = queryset.filter(department_id=user.department_id)
        return queryset.order_by("-data_joined").all()


    # 添加员工
    def create(self, request, *args, **kwargs):
        #如果用的是视图集，那么视图集会自动把request放到context中，如果直接继承APIView，那么需要手动添加
        serializer = AddStaffSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            realname = serializer.validated_data['realname']
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            #保存用户数据
            user=OAUser.objects.create_user(realname=realname, email=email, password=password)
            department = request.user.department
            user.department = department
            user.save()
            #发送激活邮件
            self.send_active_email(email)

            return Response(data={'detail':'添加员工成功'}, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'detail':list(serializer.errors.values())[0][0]}, status=status.HTTP_400_BAD_REQUEST)

    # 发送激活邮件
    def send_active_email(self, email):
        token=aes.encrypt(email)
        #/staff/active?token=xxx
        active_path=reverse('staff:active_staff')+'?'+ parse.urlencode({'token':token})
        #http://127.0.0.1:8000/staff/active?token=xxx
        #http://127.0.0.1:8000/staff/active?token=RjgSom2/sCUNAIJ/I5/0p49X5hdLD5IpNq61vJ2kj9e1vBL/hmrURC2IH8nU+L0q
        active_url=self.request.build_absolute_uri(active_path)
        #发送一个链接，让用户点击这个链接后，跳转到激活的页面，才能激活
        #为了区分用户，在发送链接的邮件中，该链接中应该要包含这个用户的邮箱
        #针对邮箱要进行加密：AES
        message=f'请点击激活链接激活账号：{active_url}'
        subject = 'XHC-OA账号激活'
        #send_mail(f'XHC-OA账号激活', recipient_list=[email], message=message,from_email=settings.DEFAULT_FROM_EMAIL)
        send_mail_task.delay(email, subject, message)



class StaffViewSet(viewsets.GenericViewSet,mixins.CreateModelMixin,mixins.ListModelMixin,mixins.UpdateModelMixin):
    queryset=OAUser.objects.all()
    pagination_class = StaffPagination
    def get_serializer_class(self):
       if self.request.method in ['GET','PUT']:
           return UserSerializer
       else:
           return AddStaffSerializer
    
    # 获取员工列表
    def get_queryset(self):
        department_id = self.request.query_params.get('department_id')
        realname = self.request.query_params.get('realname')
        date_joined = self.request.query_params.getlist('date_joined[]')
        queryset = self.queryset

        # 返回员工列表逻辑
        # 1.如果是董事会的，那么返回所有员工
        # 2.如果不是董事会的，但是是部门的leader，那么返回部门员工列表
        # 3.一般员工，抛出403 Forbidden错误

        user = self.request.user
        if user.department.name != "董事会":
            if user.uid != user.department.leader.uid:
                raise exceptions.PermissionDenied()
            else:
                queryset = queryset.filter(department_id=user.department_id)
        else:
            if department_id:
                queryset = queryset.filter(department_id=department_id)
            if realname:
                queryset = queryset.filter(realname__contains=realname)
            if date_joined:
                try:
                    start_date = datetime.strptime(date_joined[0], "%Y-%m-%d")
                    end_date = datetime.strptime(date_joined[1], "%Y-%m-%d")
                    # 将结束日期的时间设置为当天的23:59:59
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                    queryset = queryset.filter(date_joined__range=(start_date, end_date))
                except Exception:
                    pass

        return queryset.order_by("-date_joined").all()
    # 添加员工
    def create(self, request, *args, **kwargs):
        serializer = AddStaffSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            realname = serializer.validated_data['realname']
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            # 保存用户数据
            user = OAUser.objects.create_user(realname=realname, email=email, password=password)
            department = request.user.department
            user.department = department
            user.save()

            # 发送激活邮件（需要添加这个方法）
            self.send_active_email(request, email)  # 注意：这里需要传入 request

            return Response({
                'code': 201,
                'message': '添加员工成功',
                'data': {
                    'uid': user.uid,
                    'email': user.email,
                    'realname': user.realname
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'code': 400,
                'message': list(serializer.errors.values())[0][0]
            }, status=status.HTTP_400_BAD_REQUEST)

    def send_active_email(self, request, email):
        """发送激活邮件"""
        token = aes.encrypt(email)
        active_path = reverse('staff:active_staff') + '?' + parse.urlencode({'token': token})
        active_url = request.build_absolute_uri(active_path)
        message = f'请点击激活链接激活账号：{active_url}'
        subject = 'XHC-OA账号激活'
        send_mail_task.delay(email, subject, message)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True#告诉DRF只修改部分数据
        return super().update(request, *args, **kwargs)#继续执行update方法



# 测试celery
class TestCeleryView(APIView):
    def get(self, request):
        #用celery异步执行debug_task这个任务
        debug_task.delay()
        return Response({'成功'})


# 下载员工信息
class StaffDownloadView(APIView):
    def get(self, request):
        # /staff/download?pks=[x,y]
        # ['x','y'] -> json格式的字符串
        pks = request.query_params.get('pks')
        try:
            pks = json.loads(pks)
        except Exception:
            return Response({"detail": "员工参数错误！"}, status=status.HTTP_400_BAD_REQUEST)
        
        #权限检查
        try:
            current_user = request.user
            queryset = OAUser.objects
            if current_user.department.name != '董事会':
                if current_user.department.leader_id != current_user.uid:
                    return Response({'detail': "没有权限下载！"}, status=status.HTTP_403_FORBIDDEN)
                else:
                    # 如果是部门的leader，那么就先过滤为本部门的员工
                    queryset = queryset.filter(department_id=current_user.department_id)
            
            # 查询并导出数据
            queryset = queryset.filter(pk__in=pks)
            result = queryset.values("realname", "email", "department__name", 'date_joined', 'status')
            staff_df = pd.DataFrame(list(result))
            staff_df = staff_df.rename(
                columns={"realname": "姓名", "email": '邮箱', 'department__name': '部门', "date_joined": '入职日期',
                         'status': '状态'})
            response = HttpResponse(content_type='application/xlsx')
            response['Content-Disposition'] = "attachment; filename=员工信息.xlsx"

            #返回Excel文件
            with pd.ExcelWriter(response) as writer:
                staff_df.to_excel(writer, sheet_name='员工信息')
            return response
        except Exception as e:
            print(e)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# 上传员工信息
class StaffUploadView(APIView):
    def post(self, request):
        serializer = StaffUploadSerializer(data=request.data)
        # 验证数据
        if serializer.is_valid():
            file = serializer.validated_data.get('file')
            current_user = request.user
            if current_user.department.name != '董事会' or current_user.department.leader_id != current_user.uid:
                return Response({"detail": "您没有权限访问！"}, status=status.HTTP_403_FORBIDDEN)
            # 读取Excel文件中的数据
            staff_df = pd.read_excel(file)
            # 创建用户列表，用于批量创建用户
            users = []
            for index, row in staff_df.iterrows():
                # 获取部门，如果当前用户不是董事会的leader，那么就只能添加本部门的员工
                if current_user.department.name != '董事会':
                    department = current_user.department
                else:
                    try:
                        department = OAdepartment.objects.filter(name=row['部门']).first()
                        if not department:
                            return Response({"detail": f"{row['部门']}不存在！"}, status=status.HTTP_400_BAD_REQUEST)
                    except Exception as e:
                        return Response({"detail": "部门列不存在！"}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    email = row['邮箱']
                    realname = row['姓名']
                    password = "111111"
                    user = OAUser(email=email, realname=realname, department=department, status=UserStatusChoices.UNACTIVE)
                    user.set_password(password)
                    users.append(user)
                except Exception:
                    return Response({"detail": "请检查文件中邮箱、姓名、部门名称！"}, status=status.HTTP_400_BAD_REQUEST)
            # 批量创建用户
            try:
                # 原子操作（事务）
                with transaction.atomic():
                    # 统一把数据添加到数据库中
                    OAUser.objects.bulk_create(users)
            except Exception:
                return Response({"detail": "员工数据添加错误！"}, status=status.HTTP_400_BAD_REQUEST)

            # 异步给每个新增的员工发送邮件
            for user in users:
                send_active_email(request, user.email)
            return Response()
        else:
            detail = list(serializer.errors.values())[0][0]
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)


