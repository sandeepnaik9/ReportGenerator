from django.urls import path
from django.conf.urls import url
from . import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('',views.home,name="home"),
    path('logout',views.user_logout,name="logout"),
    path('register',views.register_attempt,name="register_attempt"),
    path('login',views.login_attempt,name="login_attempt"),
    path('verify/<auth_token>',views.verify,name="verify"),
    path('verify_address',views.verify_redirect,name="verify_redirect"),
    path('change_pwd',views.change_pwd,name='change_pwd'),
    path('home',views.home_main,name="home"),
    path('Contact',views.contact,name="contact"),
    path('Price',views.price,name="price"),
    path('Profile',views.profile,name="profile"),
    path('upload',views.upload_handle,name="upload")

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)