from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views

app_name='absent'

router=DefaultRouter(trailing_slash=False)#默认添加斜杠
#GET /absent
#POST /absent
#http://localhost:8000/absent/absent
router.register('absent',views.AbsentViewSet,basename='absent')
#作用为将absent视图集注册到路由中，完整路由为http://localhost:8000/absent/absent
#basename作用为为视图集生成默认的路由名称


#router.urls 为路由对象生成的路由列表;生成的完整路由列表为：
urlpatterns=[
    #http://localhost:8000/absent/type
    path('type',views.AbsentTypeView.as_view(),name='absenttype'),
    #http://localhost:8000/absent/responder
    path('responder',views.ResponderView.as_view(),name='getresponder')
]+router.urls
"""
最后生成的所有路由为：
# 手动定义的路由
GET  http://localhost:8000/absent/type           # 获取请假类型
GET  http://localhost:8000/absent/responder      # 获取审批人

# ViewSet自动生成的路由
GET  http://localhost:8000/absent/absent         # 查看自己的请假列表
GET  http://localhost:8000/absent/absent?who=sub # 查看下属的请假列表
POST http://localhost:8000/absent/absent         # 发起新请假
PUT  http://localhost:8000/absent/absent/1       # 更新ID为1的请假记录
PATCH http://localhost:8000/absent/absent/1      # 部分更新ID为1的请假记录

"""