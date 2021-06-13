from django.contrib import auth
from django.contrib.auth.forms import UsernameField
from django.contrib.auth.signals import user_logged_in
from django.http.request import validate_host
from django.http.response import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render,redirect
import pandas as pd
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from .models import Profile
from django.contrib import messages
import uuid
import json
from django.core.mail import send_mail
from django.conf import Settings, settings
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives,EmailMessage
from django.template import Context, context

# Create your views here.

def home(request):
    current_user = request.user
    user_obj = ""
    auth_token = ""
    phone = ""
    jobtitle = ""
    change = "Change Password"
    if request.user.is_authenticated:
        user_obj = Profile.objects.filter(user1_id=current_user.id).first()
        user = User.objects.filter(id=request.user.id).first()
        user.username = user.email
        user.save()
        user_d = User.objects.filter(email=request.user.email).first()
        
        if request.method == "POST":
            auth_token = str(uuid.uuid4())
            print("auth_token:",auth_token)    
            jobtitle = request.POST.get('jtitle')
            phone = request.POST.get('pnum')
            profile_obj = Profile.objects.create(user1=user,auth_token=auth_token,phone_number=phone,job_title=jobtitle,is_verified=True)
            profile_obj.save()
            if user_obj is not None:
                if not user_obj.is_verified:
                    logout(request)
        if not user.has_usable_password():
            change = "Create Password"
        


    socialaccount_obj = SocialAccount.objects.filter(provider='google', user_id=current_user.id)
    
    picture = 0
    cod = ""
    cod_msg = 'Connect'
    if len(socialaccount_obj):
            cod = "disabled"
            cod_msg = "Connected"
            picture = socialaccount_obj[0].extra_data['picture']
    user_data = 'not available'
    if user_obj is not None:
        user_data = user_obj
    
    return render(request,"index.html",{'picture':picture,'userdata':user_data,"cod":cod,'cod_msg': cod_msg,"change":change})

def register_attempt(request):
    if request.method == "POST":
        first_name = request.POST.get('finame')
        last_name = request.POST.get('laname')
        email = request.POST.get('e-id')
        password= request.POST.get('pwd')
        rpassword= request.POST.get('rpwd')
        jobtitle = request.POST.get('jtitle')
        phone = request.POST.get('pnum')
        print(first_name,last_name)
        try:
            data={}
            if User.objects.filter(email = email).first():
                data['success'] = "Email already taken"
                data['error'] = True
                return HttpResponse(json.dumps(data),content_type='application/json')
            if password != rpassword:
                data['success'] = "Password isn't matching!"
                data['error'] = True
                return HttpResponse(json.dumps(data),content_type='application/json')
            
            user_obj = User.objects.create(username=email,email=email,first_name=first_name,last_name=last_name)
            user_obj.set_password(password)
            user_obj.save()
            auth_token = str(uuid.uuid4())
            profile_obj =  Profile.objects.create(user1=user_obj, auth_token=auth_token,phone_number=phone,job_title=jobtitle)
            profile_obj.save()
            data['success'] = "Check your mail for the verification link!"
            data['error'] = False
            html_content = "html_content.html"
            print(send_email_from_app(email=email,name=first_name,auth_token=auth_token))
            return HttpResponse(json.dumps(data),content_type='application/json')
        except Exception as e:
            print(e)



def result(request):
    if request.method == "POST":
        file = request.FILES["myFile"]
        df = pd.read_excel(file)
        
        ls = [df.columns.tolist()]+df.values.tolist()    
         
    return render(request,"result.html",{'data':ls})

def login_attempt(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('passw')

        user_obj = User.objects.filter(email=email).first()
        data = {}
        if user_obj is None:
            data['success'] = "User not found"
            data['error'] = True
            return HttpResponse(json.dumps(data),content_type='application/json')
        profile_obj = Profile.objects.filter(user1=user_obj).first()

        if not profile_obj.is_verified:
            data['success'] = "Please check your mail and verify your account"
            data['error'] = True
            return HttpResponse(json.dumps(data),content_type='application/json')
        
        user = authenticate(email=email,password=password)
        
        if user is None:
            data['success'] = "Wrong password!"
            data['error'] = True
            return HttpResponse(json.dumps(data),content_type='application/json')
        print('user logged in')
        login(request, user)
        
        data['success'] = "user logged in successfylly"
        data['error'] = 'loggedin'
        return redirect('https://sandeepitnaik-reportgenerator.zeet.app/Profile')
        # return HttpResponse(json.dumps(data),content_type='application/json')

def user_logout(request):
    if request.method == "POST":
        logout(request)
    return HttpResponseRedirect(reverse('home'))


def send_email_from_app(email,name,auth_token):
    html_tpl_path = 'html_content.html'
    context_data =  {'first_name': name,'token':auth_token}
    email_html_template = get_template(html_tpl_path).render(context_data)
    email_msg = EmailMessage('Your account needs to be verified', 
                                email_html_template, 
                                'sandeepnaik9900@gmail.com',
                                [email],
                                reply_to=[email]
                                )
    # this is the crucial part that sends email as html content but not as a plain text
    email_msg.content_subtype = 'html'
    email_msg.send(fail_silently=False)


def verify_redirect(request):
    profile_obj = Profile.objects.filter(auth_token = val()).first()
    print(profile_obj.is_verified)
    if profile_obj.is_verified:
        message = "Your account has already been verified"
    else:
        message = "Your account has been verified please login"
    con = 'show'
    return render(request,"index.html",{'verify':message,'con':con})

def verify(request,auth_token):
    try:
        global val
        def val():
            return auth_token
        profile_obj = Profile.objects.filter(auth_token = auth_token).first()
        if profile_obj:
            profile_obj.is_verified = True
            profile_obj.save()
            message = "Your account has been verified please login"
            con = 'show'
            return redirect('verify_redirect')
        else:
            return redirect('/error')
    except Exception as e:
        print(e)

def change(request):
    if request.method == "POST":
        first_name = request.POST.get('firstnamec')
        last_name = request.POST.get('lastnamec')
        jobtitle = request.POST.get('jtitle')
        phone = request.POST.get('phonec')
        
        user =  User.objects.filter(email = request.user).first()
        profile = Profile.objects.filter(user1=user).first()
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        profile.phone_number = phone
        profile.job_title = jobtitle
        profile.save()
        return redirect("/")
def change_pwd(request):
    if request.method == "POST":
        data ={}
        user  = User.objects.filter(id = request.user.id).first()
        if not request.user.has_usable_password():
            create = request.POST.get("cpwd")
            r_pwd = request.POST.get("rpwd")
            
            if create != r_pwd:
                data['er'] = True
                data['success'] = "Password does not match!"
                return HttpResponse(json.dumps(data),content_type='application/json')
            if create == r_pwd:
                data['er'] = False
                data['success'] = "Password created successfully!"
                data['cont'] = "Change Password"
                user.set_password(create)
                user.save()
                return HttpResponse(json.dumps(data),content_type='application/json')
        old_pass = request.POST.get('opwd')
        new_pass = request.POST.get('npwd')
        re_pwd =  request.POST.get('rpwd')
        if not request.user.check_password(old_pass):
            data['er'] = True
            data['success'] = "Old password din't match!"
            return HttpResponse(json.dumps(data),content_type='application/json')
        if request.user.check_password(old_pass):
            if new_pass != re_pwd:
                data['er'] = True
                data['success'] = "Password does not match!"
                return HttpResponse(json.dumps(data),content_type='application/json')
        data['er'] = False
        data['success'] = "Password changed successfully!"
        
        user.set_password(new_pass)
        user.save()
        return HttpResponse(json.dumps(data),content_type='application/json')
 
def home_main(request):
    if not request.user.is_authenticated:
        return redirect("/")
    return render(request,"index.html",{'content':'home'})
def profile(request):
    current_user = request.user
    user_obj = ""
    auth_token = ""
    phone = ""
    jobtitle = ""
    change = "Change Password"
    if request.user.is_authenticated:
        user_obj = Profile.objects.filter(user1_id=current_user.id).first()
        user = User.objects.filter(id=request.user.id).first()
        user.username = user.email
        user.save()
        user_d = User.objects.filter(email=request.user.email).first()
        
        if request.method == "POST":
            auth_token = str(uuid.uuid4())
            print("auth_token:",auth_token)    
            jobtitle = request.POST.get('jtitle')
            phone = request.POST.get('pnum')
            profile_obj = Profile.objects.create(user1=user,auth_token=auth_token,phone_number=phone,job_title=jobtitle,is_verified=True)
            profile_obj.save()
            if user_obj is not None:
                if not user_obj.is_verified:
                    logout(request)
        if not user.has_usable_password():
            change = "Create Password"
        


    socialaccount_obj = SocialAccount.objects.filter(provider='google', user_id=current_user.id)
    
    picture = 0
    cod = ""
    cod_msg = 'Connect'
    if len(socialaccount_obj):
            cod = "disabled"
            cod_msg = "Connected"
            picture = socialaccount_obj[0].extra_data['picture']
    user_data = 'not available'
    if user_obj is not None:
        user_data = user_obj
    if not request.user.is_authenticated:
        return redirect("/")
    return render(request,"index.html",{'picture':picture,'userdata':user_data,"cod":cod,'cod_msg': cod_msg,"change":change,"content":"profile"})
    
def contact(request):
    if not request.user.is_authenticated:
        return redirect("/")
    return render(request,"index.html",{'content':'contact'})
def price(request):
    if not request.user.is_authenticated:
        return redirect("/")
    return render(request,"index.html",{'content':'price'})

