from rest_framework import serializers
from django.core.validators import  FileExtensionValidator,get_available_image_extensions

class UploadImageSerializer(serializers.Serializer):
    """
    图片上传序列化器
    """
    image = serializers.ImageField(
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg','gif'])],
        error_messages={'required':'请上传图片！','invalid_image':'请上传有效的图片！'}
    )

    def validate_image(self,value):
        max_size = 5*1024*1024
        size = value.size
        if size > max_size:
            raise serializers.ValidationError('图片大小不能超过5MB！')
        return value