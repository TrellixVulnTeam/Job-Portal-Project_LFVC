from django.http import HttpResponseRedirect, HttpResponse 
from django.db import connection
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.template import Context
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password

from jportal.models import Category, SubCategory, State, City, Banners_state, Banners_category
from jportal.models import Education, Graduation, Post_Graduation, PhD, AddJob
from jportal.models import Employer, EmployerCompanyProfile, Contact_Us
from jportal.models import JobSeekers, JobSeekersProfile, Appliers
from jportal.models import Subscribtion, Newsletter, SaveJobseeker

from jportal.forms import EmployerForm, JobSeekerForm, UserForm, JobForm, EmployerCompanyProfileForm
from jportal.forms import UserEditForm, EmployerEditForm, JobSeekerEditForm, ContactForm
from jportal.forms import SearchByCategory, SearchByLocation, JobseekerprofileForm, UploadResume
from jportal.forms import GraduationForm,PostGraduationForm,PhDForm,ClassXIIForm,ClassXForm

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from .tokens import account_activation_token

from datetime import datetime
import json

def user_type(ek_req):
    usertype=''
    #checking the type of user. i.e Employer or JobSeeker
    #Lame Logic -_-
    if ek_req.user:
        u = ek_req.user.id
        print(u)
        try:
            e=Employer()
            e = Employer.objects.get(user_id=u) 
            if e:
                usertype='e'
                print("Employer: ",usertype)
        except e.DoesNotExist:
            pass

        try:
            e=JobSeekers()
            e = JobSeekers.objects.get(user_id=u) 
            if e:
                usertype='j'
                print("JobSeeker: ",usertype)
        except e.DoesNotExist:
            pass

    return usertype

#index for testing purpose...!!!
def index(request):
    print(request.user)

    context_dict = {}
    context_dict['usertype'] = user_type(request)

    context_dict['searchform'] = SearchByCategory()
    context_dict['jobs'] = job_listing(request)

    ban_state = Banners_state.objects.all()
    ban_cat = Banners_category.objects.all()
    context_dict['stb'] = ban_state
    context_dict['ctb'] = ban_cat

    return render(request, 'jportal/index.html', context_dict)

def about(request):
    context_dict = {}

    return render(request, "jportal/about.html", context_dict)

def register(request):
    context_dict = {}
    
    return render(request, 'registration/register.html', context_dict)

def banner_city(request,city_id):
    usertype = user_type(request)
    c=City.objects.get(id=city_id)
    jobs = AddJob.objects.filter(city_id=city_id)
    context_dict={'jobs':jobs,'usertype':usertype}

    return render(request,"jportal/jobsbycities.html",context_dict)

def banner_cat(request,cat_id):
    usertype = user_type(request)
    c = Category.objects.get(id=cat_id)
    jobs = AddJob.objects.filter(category_id=cat_id)
    context_dict={'jobs':jobs,'usertype':usertype}

    return render(request,"jportal/jobsbycategory.html",context_dict)

#---------------------EMPLOYER REGISTRATION
def employer_reg(request):
    context_dict = {}

    user_form = UserForm()
    employer_form = EmployerForm()
    
    print(request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        employer_form = EmployerForm(request.POST, request.FILES)
        
        if employer_form.is_valid() and user_form.is_valid():    
            user = user_form.save(commit=False)
            user.username = user.email.split('@')[0]
            user.password = user_form.cleaned_data.get('password')
            user.password = make_password(user.password)
            user.is_active = False
            user.save()
            usr_obj = User.objects.get(username=user.username)
            print("aa user obj:",usr_obj)
            emp_user = employer_form.save(commit=False)
            #emp_user.contact_no = str(employer_form.contact_no)
            emp_user.user = usr_obj
            emp_user.user.city = 'Surat'
            emp_user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your Job Portal account.'
            message = render_to_string('registration/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            print(message)
            to_email = user_form.cleaned_data.get('email')
            print("aa email:",to_email)
            email = EmailMessage(mail_subject, message, to=[to_email])
            print("email object:",email)
            if(email.send()):
                print("email sent")
            else:
                print("kai error che!!")
            return redirect('index')

        else:
            print(employer_form.errors)
            print(user_form.errors)

    context_dict['employer_form'] = employer_form
    context_dict['user_form'] = user_form
    
    return render(request, 'registration/employer_register.html', context_dict)

def activate(request, uidb64, token):
    usertype = user_type(request)
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if usertype=='e':
            usr_obj = Employer.objects.get(user_id=user.id)
        else:
            usr_obj = JobSeekers.objects.get(user_id=user.id)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        usr_obj.email_verify = True
        login(request, user)
        return redirect('index')
    else:
        return HttpResponse('Activation link is invalid!')

#--------------------JOB SEEKER REGISTRATION
def jobseeker_reg(request):
    context_dict = {}
    user_form = UserForm()
    job_seek = JobSeekerForm()

    print(request)
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        job_seek = JobSeekerForm(request.POST, request.FILES)
        if user_form.is_valid() and job_seek.is_valid():
            user = user_form.save(commit=False)
            seeker_user = job_seek.save(commit=False)
            #seeker_user.contact_no = str(job_seek.contact_no)

            user.username = user.email.split('@')[0]
            user.password = user_form.cleaned_data.get('password')
            user.password = make_password(user.password)
            user.is_active = False
            user.save()
            usr_obj = User.objects.get(username=user.username)
            print("aa user obj:",usr_obj)
            seeker_user = job_seek.save(commit=False)
            seeker_user.user = usr_obj
            seeker_user.city = 'Surat'
            seeker_user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your blog account.'
            message = render_to_string('registration/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            print(message)
            to_email = user_form.cleaned_data.get('email')
            print("aa email:",to_email)
            email = EmailMessage(mail_subject, message, to=[to_email])
            print("email object:",email)
            if(email.send()):
                print("email sent")
            else:
                print("kai error che!!")
            return redirect('index')

        else:
            print(user_form.errors)
            print(job_seek.errors)
 
    context_dict['job_seek'] = job_seek 
    context_dict['user_form'] = user_form

    return render(request, 'registration/jobseeker_register.html', context_dict)


#--------------------Employer--------------
def employer_profile(request,username):
    context_dict = {}
    print(request.user)
    usertype = user_type(request)

    if request.method == 'GET':
        emp_usr = User.objects.get(username=username)
        print(emp_usr.username)

        emp_data = Employer.objects.get(user_id=emp_usr.id)
        try:
            company_data = EmployerCompanyProfile.objects.get(employer_id=emp_data.id)
        except EmployerCompanyProfile.DoesNotExist:
            company_data = ''

    company_form = EmployerCompanyProfileForm()
    context_dict['company_form'] = company_form

    if request.method == 'POST':

        emp_usr = User.objects.get(username=username)
        print(emp_usr.username)
        emp_data = Employer.objects.get(user_id=emp_usr.id)
        company_form = EmployerCompanyProfileForm(request.POST,request.FILES)

        if company_form.is_valid():
            company_data= company_form.save(commit=False) 
            company_data.employer = emp_data
            company_data.save()
            return redirect('employer_profile',username=emp_usr.username)
        else:
            print(company_data.errors)

    context_dict['company_form'] = company_form
    context_dict['emp_usr'] = emp_usr
    context_dict['emp_data'] = emp_data
    context_dict['usertype'] = usertype
    context_dict['company_data'] = company_data

    return render(request, 'jportal/employer_profile.html', context_dict)

def edit_employer_profile(request, username):
    usertype = user_type(request)
    user = User.objects.get(username=username)
    emp = Employer.objects.get(user_id=user.id)

    if request.method == "POST":
        user_form = UserEditForm(request.POST, instance=user)
        emp_form = EmployerEditForm(request.POST, request.FILES,instance=emp)

        if user_form.is_valid() and emp_form.is_valid():
            user_edit = user_form.save(commit=False)
            user_edit.username = user_edit.email
            user_edit.save()
            emp_form.save(commit=True)

            return redirect('employer_profile',username=user_edit.username)
    else:
        user_form = UserEditForm(instance=user)
        emp_form = EmployerEditForm(instance=emp)

    context_dict={'user_form':user_form, 'emp_form':emp_form,'usertype':usertype}     

    return render(request, 'jportal/emp_edit.html', context_dict)

def edit_company_details(request):
    context_dict = {}

    usertype = user_type(request)
    emp = Employer.objects.get(user_id=request.user.id)
    company = EmployerCompanyProfile.objects.get(employer_id=emp.id)

    if request.method == "POST":
        company_form = EmployerCompanyProfileForm(request.POST, request.FILES, instance=company)

        if company_form.is_valid():
            company_form.save()
        
            return redirect('employer_profile',username=request.user.username)
    else:
       company_form = EmployerCompanyProfileForm(instance=company)

    context_dict = {'company_form':company_form, 'usertype':usertype}

    return render(request, 'jportal/company_edit.html', context_dict)

#---------------JobSeeker-------------------
def jobseeker_profile(request,username):
    context_dict = {}
    print(request.user)
    usertype = user_type(request)
    if request.method == 'GET':
        user = User.objects.get(username=username)
        print(user.username)
        seeker = JobSeekers.objects.get(user_id=user.id)
        ed = show_education(user.id)
        context_dict['user'] = user
        context_dict['seeker'] = seeker
        context_dict['usertype'] = usertype 
        context_dict['ed'] = ed
    return render(request, 'jportal/jobseeker_profile.html', context_dict)

def jobseeker_edit(request,username):
    context_dict = {}
    print(username)
    usertype=user_type(request)
    user = User.objects.get(username=username)
    b = JobSeekers.objects.get(user_id=user.id)   
    print(b.id)

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, request.FILES, instance=user)
        form = JobSeekerEditForm(request.POST, request.FILES, instance=b)
        if user_form.is_valid() and form.is_valid():
                user_edit = user_form.save(commit=False)
                user_edit.username = user_edit.email
                user_edit.save()
                form.save(commit=True)
                return redirect('jobseeker_profile',username=user_edit.username)
                
        else:
            print(form.errors)

    else:
        user_form = UserEditForm(instance=user)
        form = JobSeekerEditForm(instance=b)

    context_dict['usertype'] = usertype
    context_dict['user_form'] = user_form
    context_dict['form'] = form
    return render(request, 'jportal/jobseeker_edit.html', context_dict)

def create_resume(request,username):
    print(request.user)
    usertype = user_type(request)
    context_dict={'usertype':usertype}
    jseek = JobSeekers.objects.get(user_id=request.user.id)
    try:
        jp = JobSeekersProfile.objects.get(jobseeker_id=jseek.id)
        a=1
    except:
        a=0
    
    if request.method == 'POST' and 'create' in request.POST:
        if a:
            form = JobseekerprofileForm(request.POST,instance=jp)
            if form.is_valid():
                pro.save()
                return redirect('resume', username=username)
            else:
                print(form.errors)
        else:
            form = JobseekerprofileForm(request.POST)
            if form.is_valid():
                pro = form.save(commit=False)
                pro.jobseeker = jseek
                pro.save()
                return redirect('resume', username=username)
            else:
                print(form.errors)
    else:
        if a:
            form = JobseekerprofileForm(instance=jp)
        else:
            form = JobseekerprofileForm()
        usertype=user_type(request)
    if request.method == 'POST' and 'upload' in request.POST:
        if a:
            resumefile = UploadResume(request.POST, request.FILES, instance=jp)
            if resumefile.is_valid():
                resumefile.save()
                return redirect('resume', username=username)
            else:
                print(resumefile.errors)
        else:
            resumefile = UploadResume(request.POST, request.FILES)
            if resumefile.is_valid():
                resumefile = form.save(commit=False)
                resumefile.jobseeker = jseek
                resumefile.save()
                return redirect('resume', username=username)
            else:
                print(resumefile.errors)
    else:
        if a:
            resumefile = UploadResume(instance=jp)
        else:
            resumefile = UploadResume(instance=jp)
    context_dict['form'] = form
    context_dict['file'] = resumefile
    return render(request,'jportal/create_resume.html', context_dict)

def view_resume(request,username):
    context_dict = {}
    usertype = user_type(request)
    if request.method == 'GET':
        user = User.objects.get(username=username)
        j = JobSeekers.objects.get(user_id=user.id)
        try:
            js = JobSeekersProfile.objects.get(jobseeker_id=j.id)
        except:
            js=''
        try:
            ed=Education.objects.filter(jobseeker_id=j.id).first()
        except:
            ed=''
        context_dict['user'] = user
        context_dict['j'] = j
        context_dict['js'] = js
        context_dict['ed'] = ed
        context_dict['usertype'] = usertype 
    return render(request, 'jportal/view_resume.html', context_dict)

#------------------------Jobs-------------------
def add_job(request):
    print(request.user)
    context_dict = {}

    emp = Employer.objects.get(user_id=request.user.id)
    form=JobForm()
    if request.method == 'POST':
        form = JobForm(request.POST)
        print(form)
        print(form.is_valid())
        if form.is_valid():
            a = form.save(commit=False) 
            a.employer = emp
            a.state = emp.state
            a.city = emp.city
            a.posted_date = datetime.now()
            a.save()
            return redirect('managejob')
        else:
            print(form.errors)

    context_dict['form'] = form
    context_dict['usertype'] = user_type(request)

    return render(request, 'jportal/add_job.html', context_dict)

def job_listing(request):
    print(request)
    usertype = None
    usertype = user_type(request)

    #will execute when view is called from managejob view for employer
    if request.method == 'GET' and usertype == 'e':
        try:
            emp = Employer.objects.get(user_id=request.user.id)
            jobs = AddJob.objects.filter(employer_id=emp.id)
            return jobs

        except AddJob.DoesNotExist:
            return HttpResponse("No Jobs Posted")
    
    #will be executed when 
    elif request.method == 'GET'  and "jobtitle" in request.GET: 
        try:
            cat_title = request.GET['category']
            subcat_name = ''
            # subcat_name = request.GET['subcategory']
            #print("aa job mailu :",job_title)

            if cat_title:   #getting job as per category
                cat = Category.objects.get(id=cat_title)

                if subcat_name:     #getting job as per subcategory
                    subcat = SubCategory.objects.get(id=subcat_name)                    
                    jobs = AddJob.objects.filter(subcategory_id=subcat.id)
                    return jobs
                
                jobs = AddJob.objects.filter(category_id=cat.id)            
                return jobs

        except AddJob.DoesNotExist:
            print("Category wala thi ni mailu job")

        try:
            job_title = request.GET.get('jobtitle')
            if job_title:
                job_srch = job_title.split()
                jobs = AddJob.objects.filter(slug__icontains=job_srch[0])
                return jobs
        except:
            print("Title thi pan ni mailu job")

    return ''  #none found

def job_details(request, jobslug_name):
    context_dict = {}
    usertype = None
    usertype = user_type(request)
    context_dict['user_type'] = usertype

    if request.method == "GET":

        #getting job information
        job_info = AddJob.objects.get(slug=jobslug_name)
        print(job_info)

        #checking jobseeker has applied or not
        if usertype == 'j':
            seeker = JobSeekers.objects.get(user_id=request.user.id)
            print(seeker)
            try:
                applier = Appliers.objects.get(jobseeker_id=seeker.id, job_id=job_info.id)
                context_dict['seeker'] = seeker
                context_dict['applier'] = applier

            except Appliers.DoesNotExist:
                context_dict['seeker'] = seeker

        elif usertype == 'e':
            employer = Employer.objects.get(user_id=request.user.id)
            try:
                postedjob = AddJob.objects.filter(employer_id=employer.id)
                context_dict['employer'] = employer
                context_dict['postedjob'] = postedjob

            except AddJob.DoesNotExist:
                context_dict['employer'] = employer
    
    context_dict['job_info'] = job_info
    context_dict['usertype'] = user_type(request)

    return render(request, 'jportal/job_details.html', context_dict)

@login_required
def jobs_applied(request):
    print(request)

    context_dict = {}
    if request.method == 'GET':
        seeker = JobSeekers.objects.get(user_id=request.user.id)
        applied = Appliers.objects.filter(jobseeker_id=seeker.id)
        all_jobs  =AddJob.objects.all()

        context_dict['applied_jobs'] = applied
        context_dict['all_jobs'] = all_jobs
        context_dict['usertype'] = user_type(request)

    return render(request, 'jportal/jobs_applied.html', context_dict)

@login_required
def job_apply(request, jobslug_name):
    context_dict = {}

    if request.method == "GET":
        seeker = JobSeekers.objects.get(user_id=request.user.id)
        job = AddJob.objects.get(slug=jobslug_name)
        applier = None
        try:
            applier = Appliers.objects.get(job_id=job.id, jobseeker_id=seeker.id)
        except:
            pass

        if applier:
            context_dict['applied_before'] = applier
        else:
            applier = Appliers()
            applier.date_apply = datetime.now()
            applier.status = 'pending'
            applier.job_id = job.id
            applier.jobseeker_id = seeker.id
            applier.save()

            return job_apply(request, jobslug_name)

        context_dict['applier'] = applier
    context_dict['usertype'] = user_type(request)

    return render(request, 'jportal/job_apply.html', context_dict)

@login_required
def job_applications(request):
    context_dict={}
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute('select jportal_addjob.id,title, count(jportal_appliers.id) as total_applicants from jportal_addjob, jportal_appliers where jportal_addjob.employer_id = 3 AND jportal_appliers.job_id = jportal_addjob.id group by jportal_addjob.id')
            columns = [col[0] for col in cursor.description]
            app_count = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
            cursor.execute(
                'select au.username, jportal_addjob.title, jportal_appliers.* '\
                'from auth_user, jportal_employer , jportal_addjob, jportal_appliers, jportal_jobseekers, auth_user au '\
                'where auth_user.id = jportal_employer.user_id '\
                'and jportal_appliers.jobseeker_id=jportal_jobseekers.id '\
                'and au.id = jportal_jobseekers.user_id '\
                'and jportal_employer.id=jportal_addjob.employer_id  '\
                'and jportal_addjob.id=jportal_appliers.job_id '\
                'and auth_user.id =%s' , [request.user.id])
            columns = [col[0] for col in cursor.description]
            app_info = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

        context_dict['app_count'] = app_count
        context_dict['app_info'] = app_info
        context_dict['usertype'] = user_type(request)

        try:
            context_dict['status'] = request.GET['status']
            context_dict['applier_id'] = request.GET['applier']

            applier = Appliers.objects.get(id=context_dict['applier_id'])
            applier.status = context_dict['status']
            applier.save()
        except:
            print("Except this in case its performing other fucntion.")
        # result = json.dumps(context_dict)

    return render(request, 'jportal/job_applications.html', context_dict)

@login_required
def manage_job(request):
    print(request.user)
    context_dict = {}

    if request.method == 'GET':
        context_dict['usertype'] = user_type(request)
        context_dict['jobs'] = job_listing(request)

    return render(request, 'jportal/managejob.html', context_dict) 

@login_required
def edit_job(request, addjob_title_slug):

    context_dict = {}
    b = AddJob.objects.get(slug=addjob_title_slug)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=b)
        if form.is_valid():
            form.save(commit=True)
            return redirect('managejob')

        else:
            print(form.errors)
    else:
        form = JobForm(instance=b)

    context_dict['form'] = form
    context_dict['usertype'] = user_type(request)

    return render(request, 'jportal/edit_job.html', context_dict)

@login_required
def delete_job(request,addjob_title_slug):

    try:
        a = AddJob.objects.get(slug=addjob_title_slug)
    except AddJob.DoesNotExist:
        return redirect('index.html')
    
    if a:
        AddJob.objects.get(slug=addjob_title_slug).delete()
    
    return redirect('managejob')


def search_job(request):
    context_dict = {}
    context_dict['searchform'] = SearchByCategory()
    context_dict['jobs'] = job_listing(request)
    context_dict['usertype'] = user_type(request)

    return render(request, 'jportal/search_job.html', context_dict)

def recomm_job(request):
    context_dict = {}
    if request.method == 'GET':
        try:
           a = AddJob.objects.all()
           print(a)
        except:
            return redirect('index.html')
    
        context_dict['all_job'] = a
        context_dict['usertype'] = user_type(request)
    return render(request,'jportal/recomm_job.html',context_dict)

    




#-------------------------Newsletter-------------------
def subscribe(request):
    
    if request.method == 'POST':
        subscribe = Subscribtion()
        print("POSTYOLO")
        if request.user.is_authenticated():
            print("logged in che bhai:", request.user)
            subscribe.subscriber_email = request.user.email
        else:
            print(request.GET['semail'])
            if "semail" in request:
                subscribe.subscriber_email = request.GET['semail']

        subscribe.sub_status = True
    
        subscribe.save()

def services(request):
    context_dict = {}
    print("GETYOLO")

    subscribe(request)

    return render(request, "jportal/services.html", context_dict)

#------------------Education-----------------

def add_grad(request,username):
    user = User.objects.get(username=username)
    print(user.username)
    seeker = JobSeekers.objects.get(user_id=user.id)
    try:
        g = Education.objects.get(jobseeker_id=seeker.id, category='graduation')
        t=1
    except:
        t=0
    if request.method == 'POST':
        if t:
            form = GraduationForm(request.POST,instance=g)
            if form.is_valid():
                form.save(commit=True)
                return redirect('education', username=user.username)
            else:
                print(form.errors)
        else:
            form = GraduationForm(request.POST)
            if form.is_valid():
                g_detail=form.save(commit=False)
                g_detail.jobseeker_id=seeker.id
                g_detail.category = 'graduation'
                print(g_detail.category)
                g_detail.save()
                return redirect('education', username=user.username)
            else:
                print(form.errors)
    else:
        if t:
            form = GraduationForm(instance=g)
        else:
            form = GraduationForm()
    context_dict={'form':form}    
    return render(request,'jportal/graduation.html',context_dict)
        
def add_postgrad(request,username):
    user = User.objects.get(username=username)
    print(user.username)
    seeker = JobSeekers.objects.get(user_id=user.id)
    try:
        pg = Education.objects.get(jobseeker_id=seeker.id, category='post_graduation')
        t=1
    except:
        t=0
    if request.method == 'POST':
        if t:
            form = PostGraduationForm(request.POST,instance=pg)
            if form.is_valid():
                form.save(commit=True)
                return redirect('education', username=user.username)
            else:
                print(form.errors)
        else:
            form = PostGraduationForm(request.POST)
            if form.is_valid():
                pg_detail=form.save(commit=False)
                pg_detail.jobseeker_id=seeker.id
                pg_detail.category = 'post_graduation'
                print(pg_detail.category)
                pg_detail.save()
                return redirect('education', username=user.username)
            else:
                print(form.errors)

    else:
        if t:
            form = PostGraduationForm(instance=pg)
        else:
            form = PostGraduationForm()
    return render(request, 'jportal/post_graduation.html',{'form':form})

def add_doctorate(request,username):
    user = User.objects.get(username=username)
    print(user.username)
    seeker = JobSeekers.objects.get(user_id=user.id)
    try:
        phd = Education.objects.get(jobseeker_id=seeker.id, category='phd')
        t=1
    except:
        t=0
    if request.method == 'POST':
        if t:
            form = PhDForm(request.POST,instance=phd)
            if form.is_valid():
                form.save(commit=True)
                return redirect('education', username=user.username)
            else:
                print(form.errors)
        else:
            form = PhDForm(request.POST)
            if form.is_valid():
                phd_detail=form.save(commit=False)
                phd_detail.jobseeker_id=seeker.id
                phd_detail.category = 'phd'
                print(phd_detail.category)
                phd_detail.save()
                return redirect('education', username=user.username)
            else:
                print(form.errors)
    else:
        if t:
            form = PhDForm(instance=phd)
        else:
            form = PhDForm()
    return render(request,'jportal/phd.html',{'form':form})

def add_classxii(request,username):
    user = User.objects.get(username=username)
    print(user.username)
    seeker = JobSeekers.objects.get(user_id=user.id)
    try:
        classxii = Education.objects.get(jobseeker_id=seeker.id, category='class XII')
        t=1
    except:
        t=0
    if request.method == 'POST':
        if t:
            class_xii=ClassXIIForm(request.POST,instance=classxii)
            if class_xii.is_valid():
                class_xii.save(commit=True)
                return redirect('education', username=user.username)
            else:
                print(class_xii.errors)
        else:
            class_xii=ClassXIIForm(request.POST)
            if class_xii.is_valid():
                class_xii_detail=class_xii.save(commit=False)
                class_xii_detail.jobseeker_id=seeker.id
                class_xii_detail.category = 'class XII'
                print(class_xii_detail.category)
                class_xii_detail.save()
                return redirect('education', username=user.username)
            else:
                print(class_xii.errors)
    else:
        if t:
            class_xii=ClassXIIForm(instance=classxii)
        else:
            class_xii=ClassXIIForm()
    return render(request,'jportal/class_xii.html',{'class_xii':class_xii})

def add_classx(request,username):
    user = User.objects.get(username=username)
    print(user.username)
    seeker = JobSeekers.objects.get(user_id=user.id)
    try:
        classx = Education.objects.get(jobseeker_id=seeker.id, category='class X')
        t=1
    except:
        t=0
    if request.method == 'POST':
        if t:
            class_x=ClassXForm(request.POST,instance=classx)
            if class_x.is_valid():
                class_x.save(commit=True)
                return redirect('education', username=user.username)
            else:
                print(class_x.errors)
        else:
            class_x=ClassXForm(request.POST)
            if class_x.is_valid():
                class_x_detail=class_x.save(commit=False)
                class_x_detail.jobseeker_id=seeker.id
                class_x_detail.category = 'class X'
                print(class_x_detail.category)
                class_x_detail.save()
                return redirect('education', username=user.username)
            else:
                print(class_x.errors)
    else:
        if t:
            class_x=ClassXForm(instance=classx)
        else:
            class_x=ClassXForm()
    return render(request,'jportal/class_x.html',{'class_x':class_x})

def add_education(request,username):
    print(request.user)

    context_dict ={}
    context_dict['usertype'] = user_type(request)
    return render(request, 'jportal/education.html', context_dict)

def delete_education(request,username,ed_id):

    try:
        e = Education.objects.get(id=ed_id)
    except Education.DoesNotExist:
        return redirect('jobseeker_profile',request.user.username)
    if e:
        Education.objects.get(id=ed_id).delete()
    return redirect('jobseeker_profile',request.user.username)

def show_education(user_id):
    j = JobSeekers.objects.get(user_id=user_id)
    try:
        gr = Education.objects.get(jobseeker_id=j.id, category='graduation')
    except:
        gr = ''
    try:
        pg = Education.objects.get(jobseeker_id=j.id, category='post_graduation')
    except:
        pg = ''
    try:
        phd = Education.objects.get(jobseeker_id=j.id, category='phd')
    except:
        phd = ''
    try:
        xii = Education.objects.get(jobseeker_id=j.id, category='class XII')
    except:
        xii = ''
    try:
        x = Education.objects.get(jobseeker_id=j.id, category='class X')
    except:
        x = ''
    context_dict={'gr':gr, 'pg':pg, 'phd':phd, 'xii':xii, 'x':x}
    return context_dict
#--------------------------Search Jobseeker--------------------        
def search(request,username):
    form1 = SearchByCategory()
    form2 = SearchByLocation()
    usertype=user_type(request)
    context_dict={'form1':form1,'form2':form2,'usertype':usertype}
    if request.method == 'POST':
        try:
            cat = request.POST['category']
            print(cat)
        except: cat = ''
        try:
            subcat = request.POST['subcategory']
            print(subcat)
        except: subcat = ''
        try:
            s = request.POST['state']
            print(s)
        except: s = ''
        try:
            c = request.POST['city']
            print(c)
        except: c = ''
        try:
            if cat:
                category = Category.objects.get(id=cat)
                print(category.id)
                context_dict['category'] = category
                if subcat:
                    subcategory = SubCategory.objects.get(id=subcat)
                    print(subcategory.id)
                    context_dict['subcategory'] = subcategory
        except: pass
        try:
            if s:
                state = State.objects.get(id=s)
                print(state.id)
                context_dict['state'] = state
                if c:
                    city = City.objects.get(id=c)
                    print(city.id)
                    context_dict['city'] = city
        except: pass
    return render(request,'jportal/search_jobseeker.html',context_dict)

def save_seek(request, user_id):
    try:
        a = Employer.objects.get(user_id = request.user.id)
        t = JobSeekers.objects.get(user_id= user_id)
        print(type(request.user.id), ":" , type(user_id))
    except:
        a = None
        t = None
    if a:
        SaveJobseeker.objects.get_or_create(emp = a, jobseeker=t)
        return redirect('search_jobseeker',username=request.user.username)
    return HttpResponse('Ni thay')

def saved_jobseekers(request,username):
    usertype=user_type(request)
    emp = Employer.objects.get(user_id=request.user.id)
    try:
        sj = SaveJobseeker.objects.filter(emp_id=emp.id)
    except:
        sj = ''
    context_dict={'usertype':usertype, 'list':sj}
    return render(request,'jportal/saved_jobseekers.html',context_dict)

def view_jobseeker(request,emp_username,username):
    usertype=user_type(request)
    juser = User.objects.get(username=username)
    j = JobSeekers.objects.get(user_id=juser.id)
    jp = JobSeekersProfile.objects.get(jobseeker_id=j.id)
    ed = show_education(juser.id)
    col={}
    sch={}
    for i in ed:
        if i=='gr' or i=='pg' or i=='phd':
            if ed[i]!='':
                col[i]=ed[i]
                print(col[i].category)
        else:
            if ed[i]!='':
                sch[i]=ed[i]
    context_dict={'usertype':usertype, 'j':j, 'jp':jp, 'ed':ed, 'col':col, 'sch':sch}
    return render(request,'jportal/view_jobseeker.html',context_dict)

def contact(request):
    context_dict = {}
    contact = ContactForm()
    if request.method == "POST":
        contact = ContactForm(request.POST)
        if contact.is_valid():
            contact.save()
            return redirect('index')
        else:
            print(form.errors)

    context_dict["form"] = contact
    return render(request, 'jportal/contact.html', context_dict)

def job_approval(request):
    context_dict = {}
    
    context_dict['status'] = request.GET['status']
    context_dict['applier_id'] = request.GET['applier']

    try:
        applier = Appliers.objects.get(id=context_dict['applier_id'])
        applier.status = context_dict['status']
        applier.save()
    except:
        print("Something went wrong in Appliers.")

    return HttpResponse(json.dumps(context_dict))
