import json
import requests
from django.contrib import messages
import os
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView
from django.db import transaction, IntegrityError
from django.core.mail import send_mail
from .forms import *
from .models import *
import csv
import io

def admin_home(request):
    total_guardofficeuser = GuardOfficeUser.objects.all().count()
    total_guards = Guard.objects.all().count()
    sites = Site.objects.all()
    total_site = sites.count()
    total_guard_office = GuardOffice.objects.all().count()
    attendance_list = Attendance.objects.filter(site__in=sites)
    total_attendance = attendance_list.count()
    attendance_list = []
    site_list = []
    for site in sites:
        attendance_count = Attendance.objects.filter(site=site).count()
        site_list.append(site.name[:7])
        attendance_list.append(attendance_count)
    context = {
        'page_title': "Dashboard - SmartPatrol",
        'total_guards': total_guards,
        'total_guardofficeuser': total_guardofficeuser,
        'total_guard_office': total_guard_office,
        'total_site': total_site,
        'site_list': site_list,
        'attendance_list': attendance_list

    }
    return render(request, 'ceo_template/home_content.html', context)


def add_guardofficeuser(request):
    form = GuardOfficeUserForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': 'Add Guard Office User'}
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            if not first_name.isalpha() or not last_name.isalpha():
                messages.error(request, "First and last name can only contain characters.")
                return redirect(reverse('add_guardofficeuser'))
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            guard_office = form.cleaned_data.get('guard_office')
            try:
                passport = request.FILES['profile_pic']
                fs = FileSystemStorage()
                filename = fs.save(passport.name, passport)
                passport_url = fs.url(filename)
            except KeyError:
                passport = None
                passport_url = None
                
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=2, first_name=first_name, last_name=last_name, profile_pic=passport_url)
                user.gender = gender
                user.address = address
                user.guardofficeuser.guard_office = guard_office
                user.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_guardofficeuser'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Please fulfil all requirements")

    return render(request, 'ceo_template/add_guardofficeuser_template.html', context)


def add_guard(request):
    guard_form = GuardForm(request.POST or None, request.FILES or None)
    context = {'form': guard_form, 'page_title': 'Add Guards'}
    if request.method == 'POST':
        if guard_form.is_valid():
            first_name = guard_form.cleaned_data.get('first_name')
            last_name = guard_form.cleaned_data.get('last_name')
            if not first_name.isalpha() or not last_name.isalpha():
                messages.error(request, "First and last name can only contain characters.")
                return redirect(reverse('add_guard'))
            address = guard_form.cleaned_data.get('address')
            email = guard_form.cleaned_data.get('email')
            gender = guard_form.cleaned_data.get('gender')
            password = guard_form.cleaned_data.get('password')
            guard_office = guard_form.cleaned_data.get('guard_office')
            site = guard_form.cleaned_data.get('site')
            try:
                passport = request.FILES['profile_pic']
                fs = FileSystemStorage()
                filename = fs.save(passport.name, passport)
                passport_url = fs.url(filename)
            except KeyError:
                passport = None
                passport_url = None
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=3, first_name=first_name, last_name=last_name, profile_pic=passport_url)
                user.gender = gender
                user.address = address
                user.guard.guard_office = guard_office
                user.guard.site = site
                # user.position = position
                user.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_guard'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Could Not Add: ")
    return render(request, 'ceo_template/add_guard_template.html', context)


def add_guard_bulk(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
            return redirect(reverse('add_guard_bulk'))
        
        # max_upload_size = 5242880  # 5MB
        # if csv_file.size > max_upload_size:
        #     messages.error(request, 'File is too large. Please upload a file smaller than 5MB.')
        #     return redirect(reverse('add_guard_bulk'))
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            csv_data = list(csv.DictReader(io_string, delimiter=','))
        except Exception as e:
            messages.error(request, f"Error reading the CSV file: {e}")
            return redirect(reverse('add_guard_bulk'))
        
        user_type = request.user.user_type
        total_rows = len(csv_data)
        
        # Gender mapping
        gender_map = {
            'male': 'M',
            'female': 'F'
        }
        
        for index, row in enumerate(csv_data):
            try:
                first_name = row.get('first_name', 'Default')
                last_name = row.get('last_name', 'Default')
                email = row.get('email')
                gender = gender_map.get(row.get('gender', '').lower(), 'M')  # Map gender to 'M' or 'F'
                address = row.get('address', '')
                password = '123'  
                
                if not email:
                    continue

                # Check for duplicate email
                if CustomUser.objects.filter(email=email).exists():
                    messages.warning(request, f"Duplicate email found: {email}. Skipping this entry.")
                    continue
                
                guard_office_name = row.get('guard_office')
                site_name = row.get('site')
                
                if user_type == 1:
                    guard_office_name = guard_office_name if guard_office_name else 'Custom'
                    site_name = site_name if site_name else 'Custom'
                elif user_type == 2:
                    guard_office_name = request.user.guard.guard_office.name if not guard_office_name else guard_office_name
                    site_name = None
                
                guard_office = GuardOffice.objects.get_or_create(name=guard_office_name)[0] if guard_office_name else None
                site = Site.objects.get_or_create(name=site_name, guard_office=guard_office)[0] if site_name else None
                
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    address=address,
                    user_type='3',  # Ensure user_type is a string
                    profile_pic=None  # Default to None as in bulk upload process
                )
                
                Guard.objects.create(
                    admin=user,
                    guard_office=guard_office,
                    site=site
                )
            except Exception as e:
                messages.error(request, f"Error adding guard with email {email}: {e}")
            
            # Break the loop if it is the last row
            if index == total_rows - 1:
                break
        
        messages.success(request, 'Employees added successfully.')
        return redirect(reverse('manage_guard'))
        
    return render(request, 'ceo_template/add_guard_bulk.html', {'page_title': 'Add Employees in Bulk'})

def add_guard_office(request):
    form = GuardOfficeForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Guard Office'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                guard_office = GuardOffice()
                guard_office.name = name
                guard_office.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_guard_office'))
            except:
                messages.error(request, "Could Not Add")
        else:
            messages.error(request, "Could Not Add")
    return render(request, 'ceo_template/add_guard_office_template.html', context)


def add_site(request):
    form = SiteForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Site'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            guard_office = form.cleaned_data.get('guard_office')
            try:
                site = Site()
                site.name = name
                site.guard_office = guard_office
                site.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('admin_add_site'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'ceo_template/add_site_template.html', context)

def manage_site(request):
    sites = Site.objects.all()
    context = {
        'sites': sites,
        'page_title': 'Manage Sites'
    }
    return render(request, "ceo_template/manage_site.html", context)

def manage_guardofficeuser(request):
    allguardofficeuser = CustomUser.objects.filter(user_type=2)
    context = {
        'allguardofficeuser': allguardofficeuser,
        'page_title': 'Edit Guard Office User'
    }
    return render(request, "ceo_template/manage_guardofficeuser.html", context)


def manage_guard(request):
    user = request.user

    # Check if the user is of type admin (user_type = 1)
    if user.user_type == '1':
        guards = CustomUser.objects.filter(user_type=3)
        sites = Site.objects.all()
    else:
        try:
            guardofficeuser = GuardOfficeUser.objects.get(admin=user)
            guardofficeuser_guard_office = guardofficeuser.guard_office
        except GuardOfficeUser.DoesNotExist:
            messages.error(request, "Current user is not associated with a guard office user.")
            return redirect('manage_guard')  

        guards = CustomUser.objects.filter(user_type=3, guard__guard_office=guardofficeuser_guard_office)
        sites = Site.objects.filter(guard_office=guardofficeuser_guard_office)
    
    context = {
        'guards': guards,
        'sites': sites,
        'page_title': 'Manage Guards'
    }
    return render(request, "ceo_template/manage_guard.html", context)

def manage_guard_office(request):
    guard_offices = GuardOffice.objects.all()
    context = {
        'guard_offices': guard_offices,
        'page_title': 'Manage Sites'
    }
    return render(request, "ceo_template/manage_guard_office.html", context)


def manage_site(request):
    sites = Site.objects.all()
    context = {
        'sites': sites,
        'page_title': 'Manage Sites'
    }
    return render(request, "ceo_template/manage_site.html", context)


def edit_guardofficeuser(request, guardofficeuser_id):
    guardofficeuser = get_object_or_404(GuardOfficeUser, id=guardofficeuser_id)
    user = guardofficeuser.admin

    if request.method == 'POST':
        form = GuardOfficeUserForm(request.POST, request.FILES, instance=guardofficeuser)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            passport = request.FILES.get('profile_pic')

            if password:
                user.set_password(password)
            if passport:
                fs = FileSystemStorage()
                filename = fs.save(passport.name, passport)
                user.profile_pic = fs.url(filename)

            user.save()
            guardofficeuser.save()

            messages.success(request, "Successfully Updated")
            return redirect(reverse('edit_guardofficeuser', args=[guardofficeuser_id]))
        else:
            messages.error(request, "Please fill the form properly")
    else:
        form = GuardOfficeUserForm(instance=guardofficeuser)

    context = {
        'form': form,
        'guardofficeuser_id': guardofficeuser_id,
        'page_title': 'Edit Guard Office User'
    }
    return render(request, "ceo_template/edit_guardofficeuser_template.html", context)


def edit_guard(request, guard_id):
    guard = get_object_or_404(Guard, id=guard_id)
    form = GuardForm(request.POST or None, instance=guard)
    context = {
        'form': form,
        'guard_id': guard_id,
        'page_title': 'Edit Guards'
    }
    
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            if not first_name.isalpha() or not last_name.isalpha():
                messages.error(request, "First and last name can only contain characters.")
                return redirect(reverse('add_guard'))
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            guard_office = form.cleaned_data.get('guard_office')
            site = form.cleaned_data.get('site')
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=guard.admin.id)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.username = username
                user.email = email
                if password != None:
                    user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                guard.guard_office = guard_office
                guard.site = site
                user.save()
                guard.save()
                messages.success(request, "Successfully Updated")
                
                return redirect(reverse('edit_guard', args=[guard_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly!")
    else:
        return render(request, "ceo_template/edit_guard_template.html", context)


def edit_guard_office(request, guard_office_id):
    instance = get_object_or_404(GuardOffice, id=guard_office_id)
    form = GuardOfficeForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'guard_office_id': guard_office_id,
        'page_title': 'Edit Guard Office'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                guard_office = GuardOffice.objects.get(id=guard_office_id)
                guard_office.name = name
                guard_office.save()
                messages.success(request, "Successfully Updated")
            except:
                messages.error(request, "Could Not Update")
        else:
            messages.error(request, "Could Not Update")

    return render(request, 'ceo_template/edit_guard_office_template.html', context)


def edit_site(request, site_id):
    instance = get_object_or_404(Site, id=site_id)
    form = SiteForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'site_id': site_id,
        'page_title': 'Edit Site'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            guard_office = form.cleaned_data.get('guard_office')
            try:
                site = Site.objects.get(id=site_id)
                site.name = name
                site.guard_office = guard_office
                site.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('admin_edit_site', args=[site_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'ceo_template/edit_site_template.html', context)


@csrf_exempt
def check_email_availability(request):
    email = request.POST.get("email")
    try:
        user = CustomUser.objects.filter(email=email).exists()
        if user:
            return HttpResponse(True)
        return HttpResponse(False)
    except Exception as e:
        return HttpResponse(False)


@csrf_exempt
def guard_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackGuard.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Guards Feedback Messages'
        }
        return render(request, 'ceo_template/guard_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackGuard, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()

            user_email = feedback.guard.admin.email
            subject = "Your feedback has been replied to"
            message = f"Hello {feedback.guard.admin.get_full_name()},\n\nYour feedback has received a reply: {reply}\n\nBest regards,\nSmartPatrol"
            from_email = os.environ.get('EMAIL_ADDRESS')
            send_mail(subject, message, from_email, [user_email])

            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error: {e}") 
            return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
def guardofficeuser_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackGOUser.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Guard Office User Feedback Messages'
        }
        return render(request, 'ceo_template/guardofficeuser_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackGOUser, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            
            user_email = feedback.guardofficeuser.admin.email
            subject = "Your feedback has been replied to"
            message = f"Hello {feedback.guardofficeuser.admin.get_full_name()},\n\nYour feedback has received a reply: {reply}\n\nBest regards,\nSmartPatrol"
            from_email = os.environ.get('EMAIL_ADDRESS')
            send_mail(subject, message, from_email, [user_email])
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error: {e}") 
            return JsonResponse({'status': 'error', 'message': str(e)})
        
@csrf_exempt
def client_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackClient.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Client Feedback Messages'
        }
        return render(request, 'ceo_template/client_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackClient, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
           
            user_email = feedback.client.admin.email
            subject = "Your feedback has been replied to"
            message = f"Hello {feedback.client.admin.get_full_name()},\n\nYour feedback has received a reply: {reply} To view this please click here \n\nBest regards,\nSmartPatrol"
            from_email = os.environ.get('EMAIL_ADDRESS')
            send_mail(subject, message, from_email, [user_email])
            
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)

@csrf_exempt
def view_guardofficeuser_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportGOUser.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From GO User'
        }
        return render(request, "ceo_template/guardofficeuser_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportGOUser, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


@csrf_exempt
def view_guard_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportGuard.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Employees'
        }
        return render(request, "ceo_template/guard_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportGuard, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


def admin_view_attendance(request):
    sites = Site.objects.all()
    context = {
        'sites': sites,
        'page_title': 'View Attendance'
    }

    return render(request, "ceo_template/admin_view_attendance.html", context)


@csrf_exempt
def get_admin_attendance(request):
    site_id = request.POST.get('site')
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        site = get_object_or_404(Site, id=site_id)
        attendance = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_reports = AttendanceReport.objects.filter(attendance=attendance)
        json_data = []
        for report in attendance_reports:
            data = {
                "status": str(report.status),
                "name": str(report.guard)
            }
            json_data.append(data)
        return JsonResponse(json.dumps(json_data), safe=False)
    except Exception as e:
        return None


def admin_view_profile(request):
    admin = get_object_or_404(Admin, admin=request.user)
    form = AdminForm(request.POST or None, request.FILES or None,
                     instance=admin)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                if not first_name.isalpha() or not last_name.isalpha():
                    messages.error(request, "First and last name can only contain characters.")
                    return redirect(reverse('admin_view_profile'))
                password = form.cleaned_data.get('password') or None
                passport = request.FILES.get('profile_pic') or None
                custom_user = admin.admin
                if password != None:
                    custom_user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    custom_user.profile_pic = passport_url
                custom_user.first_name = first_name
                custom_user.last_name = last_name
                custom_user.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('admin_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
    return render(request, "ceo_template/admin_view_profile.html", context)


def admin_notify_guardofficeuser(request):
    guardofficeuser = CustomUser.objects.filter(user_type=2)
    context = {
        'page_title': "Send Notifications To guardofficeuser",
        'allguardofficeuser': guardofficeuser
    }
    return render(request, "ceo_template/guardofficeuser_notification.html", context)


def admin_notify_guard(request):
    guard = CustomUser.objects.filter(user_type=3)
    context = {
        'page_title': "Send Notifications To Guards",
        'guards': guard
    }
    return render(request, "ceo_template/guard_notification.html", context)


@csrf_exempt
def send_guard_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    guard = get_object_or_404(Guard, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "SmartPatrol",
                'body': message,
                'click_action': reverse('guard_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': guard.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationGuard(guard=guard, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


@csrf_exempt
def send_guardofficeuser_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    guardofficeuser = get_object_or_404(GuardOfficeUser, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "SmartPatrol",
                'body': message,
                'click_action': reverse('guardofficeuser_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': guardofficeuser.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationGOUser(guardofficeuser=guardofficeuser, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def delete_guardofficeuser(request, guardofficeuser_id):
    guardofficeuser = get_object_or_404(CustomUser, guardofficeuser__id=guardofficeuser_id)
    guardofficeuser.delete()
    messages.success(request, "Guard Office User deleted successfully!")
    return redirect(reverse('manage_guardofficeuser'))


def delete_guard(request, guard_id):
    guard = get_object_or_404(CustomUser, guard__id=guard_id)
    guard.delete()
    messages.success(request, "Guard deleted successfully!")
    return redirect(reverse('manage_guard'))


def delete_guard_office(request, guard_office_id):
    guard_office = get_object_or_404(GuardOffice, id=guard_office_id)
    try:
        guard_office.delete()
        messages.success(request, "Guard Office deleted successfully!")
    except Exception:
        messages.error(
            request, "Sorry, some guard and users are assigned to this guard office already. Kindly change the affected guards/guard office users and try again")
    return redirect(reverse('manage_guard_office'))


def delete_site(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    site.delete()
    messages.success(request, "Site deleted successfully!")
    return redirect(reverse('admin_manage_site'))

def view_guard_location(request):
    context = {}
    return render(request, "ceo_template/view_guard_location.html",context)

def ceo_add_client(request):
    client_form = AdminClientForm(request.POST or None, request.FILES or None)
    context = {'client_form': client_form, 'page_title': 'Add Client'}

    if request.method == 'POST':
        if client_form.is_valid():
            first_name = client_form.cleaned_data.get('first_name')
            last_name = client_form.cleaned_data.get('last_name')
            if not first_name.isalpha() or not last_name.isalpha():
                messages.error(request, "First and last name can only contain characters.")
                return redirect(reverse('ceo_add_client'))
            gender = client_form.cleaned_data.get('gender')
            address = client_form.cleaned_data.get('address')
            email = client_form.cleaned_data.get('email')
            password = client_form.cleaned_data.get('password')
            site = client_form.cleaned_data.get('site')
            company_name = client_form.cleaned_data.get('company_name')
            vat_number = client_form.cleaned_data.get('vat_number')
            guard_office = client_form.cleaned_data.get('guard_office')

            if not site:
                messages.error(request, "Site field is required.")
                return render(request, 'ceo_template/add_client_template.html', context)

            try:
                with transaction.atomic():
                    user, created = CustomUser.objects.get_or_create(
                        email=email,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'gender': gender,
                            'address': address,
                            'password': password,
                            'user_type': 4
                        }
                    )

                    if not created:
                        if user.user_type != '4':
                            messages.error(request, "The user exists but is not a Client.")
                            return render(request, 'ceo_template/add_client_template.html', context)

                    if created:
                        user.set_password(password)
                        user.save()

                    client, client_created = Client.objects.get_or_create(
                        admin=user,
                        defaults={
                            'site': site,
                            'company_name': company_name,
                            'vat_number': vat_number,
                            'guard_office': guard_office
                        }
                    )

                    if not client_created:
                        client.site = site
                        client.company_name = company_name
                        client.vat_number = vat_number
                        client.guard_office = guard_office
                        client.save()

                    messages.success(request, "Successfully Added or Updated Client")
                    return redirect('ceo_add_client')

            except IntegrityError as e:
                messages.error(request, "Could Not Add: " + str(e))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))

    return render(request, 'ceo_template/add_client_template.html', context)

def ceo_manage_client(request):
    all_clients = Client.objects.select_related('admin', 'guard_office', 'site')
    guard_offices = GuardOffice.objects.all()
    context = {
        'all_clients': all_clients,
        'guard_offices': guard_offices,
        'page_title': 'Manage Clients'
    }
    return render(request, "ceo_template/manage_client_template.html", context)

def ceo_edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    user = client.admin

    if request.method == 'POST':
        form = AdminClientForm(request.POST, request.FILES, instance=client)
        if form.is_valid():
            client = form.save(commit=False)
            password = form.cleaned_data.get('password')
            profile_pic = request.FILES.get('profile_pic')

            if password:
                user.set_password(password)
            if profile_pic:
                fs = FileSystemStorage()
                filename = fs.save(profile_pic.name, profile_pic)
                user.profile_pic = fs.url(filename)

            user.save()
            client.save()

            messages.success(request, "Successfully Updated")
            return redirect(reverse('ceo_edit_client', args=[client_id]))
        else:
            messages.error(request, "Please fill the form properly")
    else:
        form = AdminClientForm(instance=client)

    context = {
        'form': form,
        'client_id': client_id,
        'page_title': 'Edit Client'
    }
    return render(request, "ceo_template/edit_client_template.html", context)

def ceo_delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    user = client.admin  # Get the associated CustomUser
    client.delete()
    user.delete()  # Delete the associated CustomUser
    messages.success(request, "Client and associated user deleted successfully.")
    return redirect('ceo_manage_client')
