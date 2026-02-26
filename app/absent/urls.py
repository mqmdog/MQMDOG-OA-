from django.urls import path,include
from rest_framework.routers import DefaultRouter #DRF路由器模块导入，自动为ViewSet生成RESTful风格的URL路由
from . import views #视图模块导入

# ┌─────────────────────────────────────────────────────────────────┐
# │                       路由架构图                                  │
# │                                                                 │
# │   手动路径 (path)              路由器 (router)                    │
# │        │                            │                           │
# │   /absent/type              /absent/absent                     │
# │   /absent/responder              │                              │
# │                                 ├── GET   (list)                │
# │                                 ├── POST  (create)              │
# │                                 ├── PUT   (update)              │
# │                                 ├── PATCH (partial_update)      │
# │                                 └── DELETE (destroy)            │
# │                                                                 │
# └─────────────────────────────────────────────────────────────────┘

# 用户请求: GET /absent/absent
#                     │
#                     ▼
#          Django URL 匹配
#          ┌─────────────────────────────────────────┐
#          │  urlpatterns = [                        │
#          │      path('type', ...),    # /absent/type│
#          │      path('responder', ...),# /absent/responder│
#          │  ] + router.urls                       │
#          │                                         │
#          │  /absent/absent 不匹配 type             │
#          │  /absent/absent 不匹配 responder       │
#          │  /absent/absent 匹配 router.urls[0]   │
#          └─────────────────────────────────────────┘
#                     │
#                     ▼
#          调用 AbsentViewSet.as_view({'get': 'list'})
#                     │
#                     ▼
#          执行 list() 方法，返回请假列表

app_name='absent'

router=DefaultRouter(trailing_slash=False)#无尾部斜杠

router.register('absent',views.AbsentViewSet,basename='absent')


#router.urls 为路由对象生成的路由列表;生成的完整路由列表为：
urlpatterns=[
    path('type',views.AbsentTypeView.as_view(),name='absenttype'),
    path('responder',views.ResponderView.as_view(),name='getresponder') #as_view()将类转换为函数视图
]+router.urls

