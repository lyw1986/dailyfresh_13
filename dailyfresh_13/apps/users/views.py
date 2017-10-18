from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import View
import re
from django.core.urlresolvers import reverse

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
            return render(request, 'register.html',{'errmg':'邮箱格式不正确'})
        if allow != 'on':
            return render(request,'register,html',{'errmg':'请接收注册协议'})

