from django.urls import path
from .import views
from rest_framework.routers import DefaultRouter

app_name = 'staff'
# trailing_slash=False 表示 URL 不带斜杠（如 /api/staff 而不是 /api/staff/）
router = DefaultRouter(trailing_slash=False)
router.register('staff',views.StaffViewSet,basename='staff')
# 方法	URL	视图	说明
# GET / api/staff	StaffViewSet.list	获取员工列表
# POST / api/staff	StaffViewSet.create	创建员工
# GET / api/staff/{pk}	StaffViewSet.retrieve	获取单个员工详情
# PUT/PATCH / api/staff/{pk}	StaffViewSet.update	更新员工
# DELETE / api/staff/{pk}	StaffViewSet.destroy	删除员工

urlpatterns = [
    path('departments',views.DepartmentListView.as_view(),name='departments'),
    # path('staff',views.StaffView.as_view(),name='staff_view'),
    path('download',views.StaffDownloadView.as_view(),name='download_staff'),
    path('upload',views.StaffUploadView.as_view(),name='upload_staff'),
    path('active',views.ActiveStaffView.as_view(),name='active_staff'),
    path('test/celery',views.TestCeleryView.as_view(),name='test_celery')
]+router.urls

# 方法	URL	视图	说明
# GET / api/departments	DepartmentListView	获取部门列表
# GET / api/download	StaffDownloadView	下载员工模板/数据
# POST / api/upload	StaffUploadView	上传员工 Excel
# POST / api/active	ActiveStaffView	激活员工账号
# GET / api/test/celery	TestCeleryView	测试 Celery 异步任务
