from rest_framework.views import APIView
from .serializer import UploadImageSerializer
from rest_framework.response import Response
from shortuuid import uuid
import os
from django.conf import settings


class UploadImageView(APIView):
    def post(self, request):
        # 1. 图片是xx.png，xx.py -> xx.png
        # 2. .png/.jpg/.jpeg, .txt/.py
        serializer = UploadImageSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data.get('image')# 获取验证后的文件对象
            # abc.png => sdfsdafsdjag + '.png'
            # os.path.splitext('abc.png') = ('abc', '.png')
            #生成新的文件名
            filename = uuid() + os.path.splitext(file.name)[-1]
            # 拼接完整保存路径
            path = settings.MEDIA_ROOT / filename # /media/sdfsdafsdjag.png
            try:
                with open(path, 'wb') as fp:
                    for chunk in file.chunks(): # 分块写入文件
                        fp.write(chunk)
            except Exception:
                return Response({
                    "errno": 1,
                    "message": "图片保存失败！"
                })
             # abc.png => /media/abc.png
            file_url = settings.MEDIA_URL + filename
            # 返回成功响应（符合 Editor.md / Markdown 编辑器图片上传格式）
            return Response({
                "errno": 0, # 注意：值是数字，不能是字符串
                "data": {
                    "url": file_url, # 图片 src ，必须
                    "alt": "", # 图片描述文字，非必须
                    "href": file_url # 图片的链接，非必须
                }
            })
        else:
            print(serializer.errors)
            return Response({
                "errno": 1, # 只要不等于 0 就行
                "message": list(serializer.errors.values())[0][0]
            })
