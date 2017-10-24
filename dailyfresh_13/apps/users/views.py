from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import View
import re
from django.core.urlresolvers import reverse
from users.models import User
from django import db
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
from celery_tasks.tasks import send_active_email
from itsdangerous import SignatureExpired

from django.contrib.auth import authenticate, login, logout
from utils.views import LoginRequiredMixin
from users.models import Address
from django_redis import get_redis_connection
from users import constants
from goods.models import GoodsSKU


# Create your views here.


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html',)

    def post(self, request):
        user_name = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        if not all([user_name, password, email]):
            return redirect(reverse('users:register'))
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请接收注册协议'})

        try:
            user = User.objects.create_user(user_name, email, password)

        except db.IntegrityError:
            return render(request, 'register.html', {'errmsg': '用户名已存在！'})

        user.is_active = False
        user.save()

        token = user.generate_active_token()

        # 使用celery异步发送邮件

        send_active_email.delay(user_name, email, token)

        return redirect(reverse('goods:index'))


class ActiveView(View):
    def get(self, request, token):
        s = Serializer(settings.SECRET_KEY)

        try:
            data = s.loads(token)
        except SignatureExpired:
            return HttpResponse('链接已过期！')

        user_id = data.get('confirm')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return HttpResponse('用户不存在！')

        user.is_active = True
        user.save()

        # return HttpResponse('进入到登陆界面')
        return redirect(reverse('users:login'))

class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self,request):
        user_name = request.POST.get('username')
        password = request.POST.get('pwd')
        remembered = request.POST.get('remembered')

        if not all([user_name, password]):
            return render(request, 'login.html')

        user = authenticate(username=user_name, password=password)
        if user is None:
            return render(request, 'login.html',{'errmsg':'用户名或密码错误！'})

        # 由于邮箱发送激活码尚未成功，所以验证是否激活先关闭
        if user.is_active is False:
            return render(request, 'login.html', {'errmsg':'用户尚未激活'})

        login(request, user)

        if remembered != 'on':
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

        next = request.GET.get('next')
        if next:
            return redirect(next)
        else:
            return redirect(reverse('goods:index'))

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))

class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user

        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None

        context ={

            'address': address
        }

        return render(request, 'user_center_site.html', context)

    def post(self, request):
        user = request.user

        recv_name = request.POST.get('recv_name')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        recv_mobile = request.POST.get('recv_mobile')

        if all([recv_name, addr, zip_code, recv_mobile]):
            Address.objects.create(
                    user=user,
                    receiver_name=recv_name,
                    detail_addr=addr,
                    zip_code=zip_code,
                    receiver_mobile=recv_mobile
                )

        return redirect(reverse('users:address'))


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user


        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None


        redis_conn = get_redis_connection('default')
        sku_ids = redis_conn.lrange('history_%s' % user.id, 0, constants.USER_HISTORY_NUM-1)


        skus = []
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            skus.append(sku)

        context = {
            'address':address,
            'skus':skus,
        }

        return render(request, 'user_center_info.html', context)








