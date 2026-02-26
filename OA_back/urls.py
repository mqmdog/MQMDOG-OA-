"""
URL configuration for OA_back project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from django.http import FileResponse
from django.views.static import serve
import os
from django.http import HttpResponseNotFound

# 自定义媒体文件视图，用于调试 request.path
def debug_media_serve(request, path):
    print(f"request.path: {request.path}")
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))
    return HttpResponseNotFound("文件不存在")


urlpatterns = [
    path('api/auth/',include('app.oaauth.url')),
    path('api/absent/',include('app.absent.urls')),
    path('api/inform/',include('app.inform.url')),
    path('api/staff/',include('app.staff.urls')),
    path('api/image/',include('app.image.urls')),
    path('api/home/',include('app.home.url')),
    # 自定义媒体文件路由，会经过中间件
    path('api/media/<path:path>', debug_media_serve),
]

# HTTP请求（如 GET /api/home/latest/inform）
#     ↓
# Django URL解析（从上往下依次匹配urlpatterns）
#     ↓
# 【步骤1】匹配主URL配置（OA_back/urls.py的urlpatterns）
#     ├─ 找到 path('api/home/', include('app.home.url'))
#     ├─ 截断前缀 'api/home/'，剩余部分 'latest/inform'
#     ↓
# 【步骤2】进入子应用URL配置（app/home/url.py的urlpatterns）
#     ├─ 继续匹配 'latest/inform'
#     ├─ 找到 path('latest/inform', views.LatestInformView.as_view(), name='latest_inform')
#     ├─ 完全匹配，找到对应的视图类
#     ↓
# 【步骤3】执行视图类
#     ├─ LatestInformView.as_view() 返回一个视图函数
#     ├─ Django自动调用该函数，传入request对象
#     ↓
# HTTP响应（JSON格式的通知数据）