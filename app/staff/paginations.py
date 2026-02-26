from rest_framework.pagination import PageNumberPagination

class StaffPagination(PageNumberPagination):
    page_query_param = 'page' # 默认的分页参数名称
    page_size_query_param = 'size' # 默认的分页大小参数名称
    page_size=2 # 默认的分页大小
