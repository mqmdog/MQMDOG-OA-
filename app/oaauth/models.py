from django.db import models #django模块相关类

from django.contrib.auth.models import User, AbstractBaseUser,PermissionsMixin, BaseUserManager# 导入Django认证系统相关类
# User: Django默认用户模型
# AbstractBaseUser: 用户模型基类，包含密码处理等核心功能
# PermissionsMixin: 权限混合类，提供权限相关功能
# BaseUserManager: 用户管理器基类
from django.contrib.auth.hashers import make_password #密码加密相关的函数
from shortuuidfield import ShortUUIDField #短UUID字段，全球唯一，用来当做主键替

# 定义用户状态的选择枚举类，定义三种属性，可以用  UserStatusChoices.属性  获取
class UserStatusChoices(models.IntegerChoices):
    ACTIVED = 1 #激活
    UNACTIVE = 2  #未激活
    LOCKED= 3 #锁定

class OAUserManager(BaseUserManager):
    """
    自定义用户管理器
    继承BaseUserManager：Django内置的用户管理器基类
    """
    use_in_migrations = True

    def _create_user(self, realname, email, password, **extra_fields):#下面的OAUser并没有定义password字段，但是其父类AbstractBaseUser定义了
        if not realname:
            raise ValueError("必须设置真实姓名")
        email = self.normalize_email(email)#规范邮箱，normalize_email()是BaseUserManager的方法
        #创建用户实例
        user = self.model(realname=realname, email=email, **extra_fields)#self.model也即OAUser user = OAUser(username=realname, email=email, **extra_fields)
        user.password = make_password(password)#对密码进行加密，make_password()将明文密码加密为Django识别的格式
        user.save(using=self._db)#保存到数据库，using=self._db 指定使用的数据库连接
        return user   #返回用户实例

    def create_user(self, realname, email=None, password=None, **extra_fields):#创建普通用户
        extra_fields.setdefault("is_staff", True)#是否是员工,默认为True
        extra_fields.setdefault("is_superuser", False)#是否是超级管理员,默认为False
        return self._create_user(realname, email, password, **extra_fields)

    def create_superuser(self,realname, email=None, password=None, **extra_fields):#创建超级管理员
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault('status', UserStatusChoices.ACTIVED)#超级管理员默认激活

        if extra_fields.get("is_staff") is not True:
            raise ValueError("用户必须设置is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("超级用户必须设置is_superuser=True.")

        return self._create_user(realname, email, password, **extra_fields)



#重写User模型，改为OAUser
class OAUser(AbstractBaseUser, PermissionsMixin):
    #用户名字段
    uid=ShortUUIDField(primary_key=True)#主键字段，使用短UUID，短uuid是一种随机字符串，全球唯一，长度为22
    realname = models.CharField(
        max_length=150,#最大长度
        unique=False,#唯一值，考虑到有同名的可能性
    )
    email = models.EmailField(unique=True, blank=False)#邮箱字段，唯一且不能为空
    telephone = models.CharField(max_length=20, blank=True)#电话号码字段
    is_staff = models.BooleanField(default=True)#是否是员工
    is_active = models.BooleanField(default=True)#是否激活
    status=models.IntegerField(choices=UserStatusChoices,default=UserStatusChoices.UNACTIVE)#用户状态字段,默认未激活，包括了上面的is_active字段，只关注status即可
    date_joined = models.DateTimeField(auto_now_add=True)#加入时间字段

    #专门做用户和部门直接绑定的关系,由于OAdepartment在OAUser后面定义，所以用字符串形式引用（在 OAUser 中引用了 OAdepartment，而 OAdepartment又引用了 OAUser。使用字符串引用来避免循环导入）
    department = models.ForeignKey('OAdepartment', null=True, on_delete=models.SET_NULL, related_name='staffs', related_query_name='staffs')

    objects = OAUserManager()#User.objects.all()的由来，依旧重写

    EMAIL_FIELD = "email"
    #USERNAME_FIELD是用来做鉴别权限的字段，邮箱不会重复，而用户名可能重复，会把authenticate中的username参数传递给USERNAME_FIELD指定的字段进行鉴别
    #from django.contrib.auth import authenticate
    #authenticate(request, username='xxx@qq.com', password='xxx')  # 这里的username要传email字段，不必去authenticate类中修改，这里改成USERNAME_FIELD = "email"即可实现
    USERNAME_FIELD = "email"
    #指定哪些字段是必须的，但是不能重复包含USERNAME_FIELD和EMAIL_FIELD已经设置过的值
    REQUIRED_FIELDS = ["realname",'password']#到了这一步，以后在创建用户时，email、realname和password都是必填的

    def clean(self):#clean方法用于在保存模型之前对数据进行清理和验证
        super().clean()#调用父类的clean方法
        self.email = self.__class__.objects.normalize_email(self.email)#规范化邮箱

    def get_full_name(self):
        return self.realname#返回用户名

    def get_short_name(self):
        return self.realname#返回用户名


class OAdepartment(models.Model):
    """
    部门模型
    """
    name=models.CharField(max_length=100)#部门名称
    intro=models.CharField(max_length=200)#部门简介
    #leader 张运营、林技术
    # 部门领导，一对一关系，一个leader只能领导一个部门，当leader被删除时，部门的leader字段设为null，related_name用于查询，related_query_name用于跨表查询
    leader=models.OneToOneField(OAUser,null=True,on_delete=models.SET_NULL,related_name='leader_department',related_query_name='leader_department')
    #manager 李经理、王总监
    # 部门经理，外键关系，一个经理可以管理多个部门，当经理被删除时，部门的manager字段设为null，related_name用于查询，related_query_name用于跨表查询
    manager=models.ForeignKey(OAUser,null=True,on_delete=models.SET_NULL,related_name='manager_departments',related_query_name='manager_departments')
