import logging

from django.contrib.auth import get_user_model
from django_python3_ldap.auth import LDAPBackend

from .models import UserProfile

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomLDAPBackend(LDAPBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print(
            "CustomLDAPBackend authenticate: {0}, {1}, {2}".format(
                username, password, kwargs
            )
        )
        # 首先使用父类的 authenticate 方法尝试通过 LDAP 认证用户
        try:
            user = super().authenticate(request, username, password, **kwargs)
        except Exception as e:
            logger.error(f"Error during authentication for user {username}: {e}")
            # 根据需要处理异常

        if user:
            print("auth user: ", user)
            # 如果用户通过 LDAP 认证，检查是否需要在 Django 中创建或更新用户
            try:
                # 尝试获取现有的 Django 用户
                django_user = User.objects.get(username=username)
            except User.DoesNotExist:
                print("User.DoesNotExist")
                django_user = User.objects.create_user(username=username)
                # 这里可以设置其他用户属性，例如 email、first_name 等
                # "username": "sAMAccountName",
                # "email": "mail",
                # "first_name": "givenName",
                # "last_name": "sn",
                django_user.email = user.mail
                django_user.first_name = user.givenName
                django_user.last_name = user.sn
                django_user.department = user.department
                django_user.country = user.co
                django_user.created = user.whenCreated
                django_user.save()

            # 在这里更新或创建 UserProfile
            user_profile, created = UserProfile.objects.get_or_create(user=django_user)
            # 这里可以设置或更新 UserProfile 的额外字段
            user_profile.employee_id = user.employeeID
            user_profile.title = user.title
            user_profile.disp_name = user.displayName
            user_profile.save()

            return django_user

        print("CustomLDAPBackend authenticate return None")
        return None
