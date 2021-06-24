from django.db.models.fields import files
from mainproject.settings import MEDIA_ROOT
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
import os
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
import numpy as np
import re


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
        
        return redirect('profile')

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
        
        return HttpResponse(json.dumps(data),content_type='application/json')

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
@csrf_exempt
def upload_handle(request):
    data = {}
    
   
    profile = User.objects.filter(email=request.user.email).first()
    print(profile.email)
    if request.method == "POST":
        File = request.FILES['uploadfile']
        ST_sheet = request.POST.get("ST_sheet")
        SA_sheet = request.POST.get("SA_sheet")
        ST_store_number = request.POST.get("ST_store_number")
        SA_store_number = request.POST.get("SA_store_number")
        ST_model = request.POST.get("ST_model")
        SA_model = request.POST.get("SA_model")
        ST_total = request.POST.get("ST_total")
        SA_total = request.POST.get("SA_total")
        models = request.POST.get("models")
        models = models.split(",")
        file_name = request.POST.get("file_name")
    
    df = excel_generate(File,ST_sheet,SA_sheet,ST_store_number,SA_store_number,ST_model,SA_model,ST_total,SA_total,models)
    # document = Uploaded_file.objects.create(user2=profile, file=File)
    # document.save()
    with BytesIO() as b:
        # Use the StringIO object as the filehandle.
        writer = pd.ExcelWriter(b, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1',index=False)
        writer.save()
        # Set up the Http response.
        filename = file_name
        response = HttpResponse(
            b.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        print("Report Generated")
        return response
def excel_generate(file,stock_sheet,sale_sheet,stock_store_number,sale_store_number,stock_model,sale_model,stock_total,sale_total,models):
    df = pd.read_excel(file,sale_sheet)
    print("df1")
    
    df2 = pd.read_excel(file,stock_sheet)
    store_code = [9131,8829,8769,8824,8822,8827,8961,'TR67','TB83',6311,7461,6627,8661,8959,7989,'T751',7656,'TJY0',8697,7907,'T750',9136,'TP56',8763,8815,7532,'TR12',7568,'TIY6',7558,8836,'T556',8825,7950,7853,'TU49',8823,'TGJ6',8742,7566,'TV17',8834,8731,8813,8675,7828,8768,8474,'TY19',6362,'T766',7835,7969,7530,'TK86',7569,3611,3696,3756,3883,6024,6262,6280,6304,6322,6350,6377,6379,6405,6410,6437,6483,6545,6650,6651,6654,6657,6660,6674,6740,6749,6785,6808,6832,6839,6917,7479,7529,7546,7553,7577,7578,7612,7649,7657,7672,7730,7733,7785,7786,7800,7810,7814,7854,7927,7966,8475,8674,8679,8736,8967,9183,9184,9186,9505,9506,'T666','T754','TC79','TEZ6','TH21','TI04','TI05','TJR0','TM91','TO50','TU16','TW84','TW86','TX53','TY23','TY90']
    df3 = pd.DataFrame()
    df = df[df[sale_store_number].isin(store_code)]
    
    df[sale_model] = df[sale_model].map(lambda x: re.sub(r'\W+', ' ',x))
    df[sale_model] = df[sale_model].map(lambda x: str(x).strip())
    print(df)
    df = df[df[sale_model].isin(models)]
    
    df = pd.pivot_table(df,index=[sale_store_number,sale_model],values=sale_total,aggfunc='sum')
    df = df.reset_index()
    
    df['store_model'] = df[sale_store_number].astype(str)+'-'+df[sale_model]
    df['store_model'] = df['store_model'].apply(lambda x:str(x).strip())
    print('df1')
    print(df)

    print('df2')
    df2 = df2[df2[stock_store_number].isin(store_code)]
    df2[stock_model] = df2[stock_model].str.replace('\\W'," ")
    df2 = df2[df2[stock_model].isin(models)]
    df2 = pd.pivot_table(df2,index=[stock_store_number,stock_model],values=stock_total,aggfunc=np.sum)
    df2 = df2.reset_index()
    
    df2['store_model'] = df2[stock_store_number].astype(str)+'-'+df2[stock_model]
    df2['store_model'] = df2['store_model'].apply(lambda x:str(x).strip())
    print(df2)
    
    df3['store_model'] = pd.concat([df['store_model'],df2['store_model']],axis=0,ignore_index=True)
    df3 =  df3.drop_duplicates()
    df3 = df3.reset_index()
    df3 = df3.merge(df2,on='store_model',how='outer',suffixes=('_stock','_sale')).merge(df,on='store_model',how='outer',suffixes=('_stock','_sale'))
    df3.drop([sale_store_number,stock_store_number,sale_model,stock_model],axis=1,inplace=True)
    df3[['Store Code','Model']] = df3.store_model.str.split("-",expand=True)
    df3.drop('store_model',axis=1,inplace=True)

    df3.fillna(0,inplace=True)
    pd.set_option('precision',0)
    # df3.astype({'AVAIL_QTY':'int64','SALE_QTY':'int64'})
    df3['Stock Gap'] = df3[stock_total] - df3[sale_total]
    df3 = df3.rename(columns={stock_total:'Stock',sale_total:'Sale'})
    df3 = pd.pivot_table(df3,index=['Store Code','Model'],values=['Stock','Sale','Stock Gap'],aggfunc=np.sum)
    df3 = df3.reset_index()
    df3 = df3[['Store Code','Model','Stock','Sale','Stock Gap']]
    
    return df3
