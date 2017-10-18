from django.conf.urls import url, include
from users import views
urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view(), name='register')
]