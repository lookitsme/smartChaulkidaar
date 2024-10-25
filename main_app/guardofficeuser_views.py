import json
from django.db import transaction, IntegrityError
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .forms import *
from .models import *
import csv, io
from django.core.mail import send_mail
import os 
from django.utils import timezone

MAX_RADIUS = 1000

def guardofficeuser_home(request):
    guardofficeuser = get_object_or_404(GuardOfficeUser, admin=request.user)
    total_guards = Guard.objects.filter(guard_office=guardofficeuser.guard_office).count()
    total_leave = LeaveReportGOUser.objects.filter(guardofficeuser=guardofficeuser).count()
    sites = Site.objects.filter(guard_office=guardofficeuser.guard_office)
    total_site = sites.count()
    attendance_list = Attendance.objects.filter(site__in=sites)
    total_attendance = attendance_list.count()
    attendance_list = []
    site_list = []
    for site in sites:
        attendance_count = Attendance.objects.filter(site=site).count()
        site_list.append(site.name)
        attendance_list.append(attendance_count)
    
    context = {
        'page_title': 'Guard Manager Panel - ' + str(guardofficeuser.admin.last_name) + ' (' + str(guardofficeuser.guard_office) + ')',
        'total_guards': total_guards,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_site': total_site,
        'site_list': site_list,
        'attendance_list': attendance_list,
        'name': guardofficeuser.guard_office.name,
        
    }
    return render(request, 'guardofficeuser_template/home_content.html', context)


def guardofficeuser_take_attendance(request):
    guardofficeuser = get_object_or_404(GuardOfficeUser, admin=request.user)
    sites = Site.objects.filter(guard_office=guardofficeuser.guard_office)
    context = {
        'sites': sites,
        'page_title': 'Take Attendance'
    }

    return render(request, 'guardofficeuser_template/guardofficeuser_take_attendance.html', context)


@csrf_exempt
def get_guards(request):
    site_id = request.POST.get('site')
    try:
        site = get_object_or_404(Site, id=site_id)
        guards = Guard.objects.filter(site=site)  # Filter by site
        guard_data = []
        for guard in guards:
            data = {
                "id": guard.id,
                "name": guard.admin.last_name + " " + guard.admin.first_name
            }
            guard_data.append(data)
        return JsonResponse(guard_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def save_attendance(request):
    guard_data = request.POST.get('guard_ids')
    date = request.POST.get('date')
    site_id = request.POST.get('site')
    guards = json.loads(guard_data)
    
    try:
        site = get_object_or_404(Site, id=site_id)
        attendance, created = Attendance.objects.get_or_create(site=site, date=date)

        for guard_dict in guards:
            guard = get_object_or_404(Guard, id=guard_dict.get('id'))
            attendance_report, report_created = AttendanceReport.objects.get_or_create(guard=guard, attendance=attendance)
            attendance_report.status = guard_dict.get('status')

            # Check if hours are provided and convert to float, default to 8 if empty
            hours = guard_dict.get('hours', '8')
            if hours.strip():  # Check if hours are not empty or just spaces
                hours = float(hours)
                if hours > 24:
                    return JsonResponse({'error': f'Hours cannot exceed 24 for guard {guard.id} on date {date}'}, status=400)
                attendance_report.duration = timedelta(hours=hours)
            else:
                attendance_report.duration = timedelta(hours=8)

            attendance_report.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def guardofficeuser_update_attendance(request):
    guardofficeuser = get_object_or_404(GuardOfficeUser, admin=request.user)
    sites = Site.objects.filter(guard_office=guardofficeuser.guard_office)
    context = {
        'sites': sites,
        'page_title': 'Update Attendance'
    }

    return render(request, 'guardofficeuser_template/guardofficeuser_update_attendance.html', context)


@csrf_exempt
def get_guard_attendance(request):
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    site_id = request.POST.get('site')

    try:
        site = get_object_or_404(Site, id=site_id)
        guards = Guard.objects.filter(site=site)
        guard_data = []

        # Create date range list
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        date_range = [(start_date_obj + timedelta(days=x)).strftime('%Y-%m-%d') for x in range((end_date_obj - start_date_obj).days + 1)]

        for guard in guards:
            attendance_data = {date: {'status': False, 'hours': 0} for date in date_range}
            total_duration = timedelta(0)

            # Fetch data from AttendanceReport
            reports = AttendanceReport.objects.filter(attendance__site=site, attendance__date__range=[start_date, end_date], guard=guard)
            for report in reports:
                date = report.attendance.date.strftime('%Y-%m-%d')
                attendance_data[date] = {
                    'status': report.status,
                    'hours': report.duration.total_seconds() / 3600
                }
                if report.status:
                    total_duration += report.duration

            # Fetch data from AttendanceLog
            logs = AttendanceLog.objects.filter(guard=guard, check_in_time__date__range=[start_date, end_date])
            for log in logs:
                date = log.check_in_time.strftime('%Y-%m-%d')
                if date not in attendance_data:
                    attendance_data[date] = {'status': log.is_approved, 'hours': 0}
                if log.is_approved:
                    total_duration += log.duration
                    attendance_data[date]['hours'] = log.duration.total_seconds() / 3600

            guard_data.append({
                'id': guard.id,
                'name': guard.admin.get_full_name(),
                'attendance': attendance_data,
                'total_hours': total_duration.total_seconds() / 3600
            })

        return JsonResponse(guard_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
def update_attendance(request):
    if request.method == 'POST':
        try:
            attendance_data = json.loads(request.POST.get('attendance_data'))
            site_id = request.POST.get('site')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')

            site = get_object_or_404(Site, id=site_id)

            for guard_id, dates in attendance_data.items():
                guard = get_object_or_404(Guard, id=guard_id)

                for date_str, status in dates.items():
                    date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                    attendance, created = Attendance.objects.get_or_create(site=site, date=date)
                    attendance_report, report_created = AttendanceReport.objects.get_or_create(
                        guard=guard, attendance=attendance
                    )
                    attendance_report.status = bool(int(status))
                    attendance_report.save()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)
    

    
# def guardofficeuser_apply_leave(request):
#     form = LeaveReportGOUserForm(request.POST or None)
#     guardofficeuser = get_object_or_404(GuardOfficeUser, admin_id=request.user.id)
#     context = {
#         'form': form,
#         'leave_history': LeaveReportGOUser.objects.filter(guardofficeuser=guardofficeuser),
#         'page_title': 'Apply for Leave'
#     }
#     if request.method == 'POST':
#         if form.is_valid():
#             try:
#                 obj = form.save(commit=False)
#                 obj.guardofficeuser = guardofficeuser
#                 obj.save()
#                 messages.success(
#                     request, "Application for leave has been submitted for review")
#                 return redirect(reverse('guardofficeuser_apply_leave'))
#             except Exception:
#                 messages.error(request, "Could not apply!")
#         else:
#             messages.error(request, "Form has errors!")
#     return render(request, "guardofficeuser_template/guardofficeuser_apply_leave.html", context)


def guardofficeuser_feedback(request):
    form = FeedbackGOUserForm(request.POST or None)
    guardofficeuser = get_object_or_404(GuardOfficeUser, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackGOUser.objects.filter(guardofficeuser=guardofficeuser),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.guardofficeuser = guardofficeuser
                obj.save()

                # Retrieve all admin emails
                try:
                    admins = CustomUser.objects.filter(user_type=1)
                    admin_emails = [admin.email for admin in admins]

                    # Send email notification to all admins
                    subject = f"New feedback submitted by {guardofficeuser.admin.get_full_name()}"
                    message = f"Hello Admin,\n\nNew feedback has been submitted by Guard Office User {guardofficeuser.admin.get_full_name()}.\n\nFeedback: {obj.feedback}\n\nBest regards,\nSmartPatrol"
                    from_email = os.environ.get('EMAIL_ADDRESS')
                    send_mail(subject, message, from_email, admin_emails)

                    messages.success(request, "Feedback submitted for review")
                except Exception as e:
                    print(f"Error sending email: {str(e)}")  # Log the error for debugging
                    messages.error(request, "Feedback submitted but email could not be sent!")

                return redirect(reverse('guardofficeuser_feedback'))
            except Exception as e:
                print(f"Error saving feedback: {str(e)}")  # Log the error for debugging
                messages.error(request, "Could not submit feedback!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "guardofficeuser_template/guardofficeuser_feedback.html", context)


def guardofficeuser_view_profile(request):
    guardofficeuser = get_object_or_404(GuardOfficeUser, admin=request.user)
    form = GOUserEditForm(request.POST or None, request.FILES or None,instance=guardofficeuser)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                if not first_name.isalpha() or not last_name.isalpha():
                    messages.error(request, "First and last name can only contain characters.")
                    return redirect(reverse('guardofficeuser_view_profile'))
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = guardofficeuser.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                guardofficeuser.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('guardofficeuser_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "guardofficeuser_template/guardofficeuser_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
            return render(request, "guardofficeuser_template/guardofficeuser_view_profile.html", context)

    return render(request, "guardofficeuser_template/guardofficeuser_view_profile.html", context)


@csrf_exempt
def guardofficeuser_fcmtoken(request):
    token = request.POST.get('token')
    try:
        guardofficeuser_user = get_object_or_404(CustomUser, id=request.user.id)
        guardofficeuser_user.fcm_token = token
        guardofficeuser_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def guardofficeuser_view_notification(request):
    guardofficeuser = get_object_or_404(GuardOfficeUser, admin=request.user)
    notifications = NotificationGOUser.objects.filter(guardofficeuser=guardofficeuser)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "guardofficeuser_template/guardofficeuser_view_notification.html", context)


def guardofficeuser_add_salary(request):
    guardofficeuser = get_object_or_404(GuardOfficeUser, admin=request.user)
    sites = Site.objects.filter(guard_office=guardofficeuser.guard_office)
    context = {
        'page_title': 'Salary Upload',
        'sites': sites
    }
    if request.method == 'POST':
        try:
            guard_id = request.POST.get('guard_list')
            site_id = request.POST.get('site')
            base = request.POST.get('base')
            ctc = request.POST.get('ctc')
            guard = get_object_or_404(Guard, id=guard_id)
            site = get_object_or_404(Site, id=site_id)
            try:
                data = GuardSalary.objects.get(
                    guard=guard, site=site)
                data.ctc = ctc
                data.base = base
                data.save()
                messages.success(request, "Scores Updated")
            except:
                salary = GuardSalary(guard=guard, site=site, base=base, ctc=ctc)
                salary.save()
                messages.success(request, "Scores Saved")
        except Exception as e:
            messages.warning(request, "Error Occured While Processing Form")
    return render(request, "guardofficeuser_template/guardofficeuser_add_salary.html", context)


@csrf_exempt
def fetch_guard_salary(request):
    try:
        site_id = request.POST.get('site')
        guard_id = request.POST.get('guard')
        guard = get_object_or_404(Guard, id=guard_id)
        site = get_object_or_404(Site, id=site_id)
        salary = GuardSalary.objects.get(guard=guard, site=site)
        salary_data = {
            'ctc': salary.ctc,
            'base': salary.base
        }
        return JsonResponse(salary_data)  # Use JsonResponse for JSON data
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def add_guard(request):
    guard_form = GuardForm(request.POST or None, request.FILES or None)
    context = {'guard_form': guard_form, 'page_title': 'Add Guard'}
    if request.method == 'POST':
        if guard_form.is_valid():
            first_name = guard_form.cleaned_data.get('first_name')
            last_name = guard_form.cleaned_data.get('last_name')
            if not first_name.isalpha() or not last_name.isalpha():
                messages.error(request, "First and last name can only contain characters.")
                return render(request, 'guardofficeuser_template/add_guard_template.html', context)
            address = guard_form.cleaned_data.get('address')
            email = guard_form.cleaned_data.get('email')
            gender = guard_form.cleaned_data.get('gender')
            password = guard_form.cleaned_data.get('password')
            guard_office = request.user.guardofficeuser.guard_office  # Set guard_office to current user's guard_office
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
    return render(request, 'guardofficeuser_template/add_guard_template.html', context)

def add_client(request):
    # print("Request method:", request.method)
    # print("Form data:", request.POST)

    try:
        guardofficeuser = GuardOfficeUser.objects.get(admin=request.user)
    except GuardOfficeUser.DoesNotExist:
        messages.error(request, "Current user is not associated with a guard office.")
        return redirect('guardofficeuser_add_client')  

    client_form = ClientForm(request.POST or None, request.FILES or None)
    context = {'client_form': client_form, 'page_title': 'Add Client'}

    if request.method == 'POST':
        if client_form.is_valid():
            # print("Form is valid")
            cleaned_data = client_form.cleaned_data
            # print("Cleaned data:", cleaned_data)

            first_name = cleaned_data.get('first_name')
            last_name = cleaned_data.get('last_name')
            if not first_name.isalpha() or not last_name.isalpha():
                messages.error(request, "First and last name can only contain characters.")
                return redirect(reverse('guardofficeuser_add_client'))
            gender = cleaned_data.get('gender')
            address = cleaned_data.get('address')
            email = cleaned_data.get('email')
            password = cleaned_data.get('password')
            site = cleaned_data.get('site')
            company_name = cleaned_data.get('company_name')
            vat_number = cleaned_data.get('vat_number')
            guard_office = guardofficeuser.guard_office  # Set guard office from current user

            # print(f"Site: {site}, Site ID: {site.pk if site else 'None'}")
            # print(f"Site instance type: {type(site)}")

            if not site:
                messages.error(request, "Site field is required.")
                return render(request, 'guardofficeuser_template/add_client_template.html', context)

            try:
                with transaction.atomic():
                    # Create the CustomUser without triggering the signal
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
                            print("User exists but is not a Client:", email)
                            return render(request, 'guardofficeuser_template/add_client_template.html', context)

                    # print("CustomUser ID:", user.pk)

                    if created:
                        user.set_password(password)
                        user.save()

                    # print("Creating or updating Client for CustomUser ID:", user.pk)

                    # Manually create and save the Client instance
                    client = Client(
                        admin=user,
                        site=site,
                        company_name=company_name,
                        vat_number=vat_number,
                        guard_office=guard_office
                    )
                    # print(f"Before saving Client: admin_id={user.pk}, site_id={site.pk}, company_name={company_name}, vat_number={vat_number}, guard_office_id={guard_office.pk if guard_office else 'None'}")
                    client.save()
                    # print("Client created with ID:", client.pk, "Site ID:", client.site.pk)

                    # Confirm the site is set correctly
                    # print(f"Client Site after save: {client.site}, Site ID: {client.site.pk}")

                    messages.success(request, "Great Success!")
                    return redirect('guardofficeuser_add_client')

            except IntegrityError as e:
                # print("IntegrityError occurred:", str(e))
                messages.error(request, "Could Not Add: " + str(e))
            except Exception as e:
                # print("Exception occurred:", str(e))
                messages.error(request, "Could Not Add: " + str(e))
        else:
            print("Form is not valid:", client_form.errors)

    return render(request, 'guardofficeuser_template/add_client_template.html', context)

def manage_client(request):
    try:
        guardofficeuser = GuardOfficeUser.objects.get(admin=request.user)
        guard_office = guardofficeuser.guard_office
        context = {
        'guardofficeuser': guardofficeuser,
        'guard_office': guard_office,
        'page_title': 'Manage Clients'
        }
        # print(f"GuardOfficeUser: {guardofficeuser}")
        # print(f"Guard Office: {guard_office}")
    except GuardOfficeUser.DoesNotExist:
        guard_office = None
        print("GuardOfficeUser.DoesNotExist", context)
    
    all_clients = Client.objects.select_related('admin').filter(guard_office=guard_office)
    # print(f"Number of clients retrieved: {all_clients.count()}")
    # for client in all_clients:
    #     print(f"Client: {client.admin.email}, Company: {client.company_name}, Guard Office: {client.guard_office}")

    sites = Site.objects.all()
    
    context = {
        'all_clients': all_clients,
        'sites': sites,
        'page_title': 'Manage Clients'
    }
    return render(request, "guardofficeuser_template/manage_client.html", context)


from django.http import Http404


def edit_client(request, client_id):
    # print(f"Received client_id: {client_id}")  # Debugging line
    try:
        client = get_object_or_404(Client, id=client_id)
        user = client.admin
        # print(f"Client found: {client}")  # Debugging line
        # print(f"Client admin: {client.admin}")
        # print(f"Client site: {client.site}")
    except Client.DoesNotExist:
        # print(f"No Client matches the given query for id {client_id}.")
        raise Http404("No Client matches the given query.")
    
    

    if request.method == 'POST':
        form = ClientForm(request.POST, request.FILES, instance=client)
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
            return redirect(reverse('guardofficeuser_edit_client', args=[client_id]))
        else:
            messages.error(request, "Please fill the form properly")
    else:
        form = ClientForm(instance=client)

    context = {
        'form': form,
        'client_id': client_id,
        'page_title': 'Edit Client'
    }
    return render(request, "guardofficeuser_template/edit_client_template.html", context)

def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    user = client.admin  # Get the associated CustomUser
    client.delete()
    user.delete()  # Delete the associated CustomUser
    messages.success(request, "Client and associated user deleted successfully.")
    return redirect('guardofficeuser_manage_client')

@csrf_exempt
def check_email_availability(request):
    if request.method == 'POST':
        email = request.POST.get("email", "").strip().lower()
        # print(f"Checking email: {email}")  # Debugging line
        user_exists = CustomUser.objects.filter(email__iexact=email).exists()
        # print(f"User exists: {user_exists}")  # Debugging line
        return JsonResponse({"available": not user_exists})
    return JsonResponse({"available": False})

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
                return redirect(reverse('guardofficeuser_edit_guard', args=[guard_id]))
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
                return redirect(reverse('guardofficeuser_manage_guard'))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly!")
    else:
        return render(request, "guardofficeuser_template/edit_guard_template.html", context)

    

def manage_guard(request):
    try:
        guardofficeuser = GuardOfficeUser.objects.get(admin=request.user)
        guardofficeuser_guard_office = guardofficeuser.guard_office
    except GuardOfficeUser.DoesNotExist:
        messages.error(request, "Current user is not associated with a guardofficeuser.")
        return redirect('some_error_page')  # Replace with your error page or desired behavior

    guards = CustomUser.objects.filter(user_type=3, guard__guard_office=guardofficeuser_guard_office)
    sites = Site.objects.filter(guard_office=guardofficeuser_guard_office)
    
    context = {
        'guards': guards,
        'sites': sites,
        'page_title': 'Manage Guards'
    }
    return render(request, "guardofficeuser_template/manage_guard.html", context)


@csrf_exempt
def assign_guards_to_site(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        guard_ids = data.get('guards')
        site_id = data.get('site_id')

        if not guard_ids or not site_id:
            return JsonResponse({'success': False, 'message': 'Invalid data provided.'}, status=400)

        site = Site.objects.get(id=site_id)
        guards = Guard.objects.filter(id__in=guard_ids)
        guards.update(site=site)

        return JsonResponse({'success': True, 'message': 'Guards assigned successfully.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)
    
def delete_guard(request, guard_id):
    guard = get_object_or_404(CustomUser, guard__id=guard_id)
    guard.delete()
    messages.success(request, "Employee deleted successfully!")
    return redirect(reverse('guardofficeuser_manage_guard'))

def add_guard_bulk(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')

        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file. Max file size is 5MB.')
            return redirect(reverse('add_guard_bulk'))
        
        max_upload_size = 5242880  # 5MB
        if csv_file.size > max_upload_size:
            messages.error(request, 'File is too large. Please upload a file smaller than 5MB.')
            return redirect(reverse('add_guard_bulk'))
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            csv_data = list(csv.DictReader(io_string, delimiter=','))
            
        except Exception as e:
            messages.error(request, f"Error reading the CSV file: {e}")
            return redirect(reverse('add_guard_bulk'))

        total_rows = len(csv_data)

        # Gender mapping
        gender_map = {
            'male': 'M',
            'female': 'F'
        }

        # Check if the user is a guardofficeuser and get their guard_office
        try:
            guardofficeuser = GuardOfficeUser.objects.get(admin=request.user)
            guardofficeuser_guard_office = guardofficeuser.guard_office
            # print(f"Guard Office User found: {guardofficeuser}, guard_office: {guardofficeuser_guard_office}")
        except GuardOfficeUser.DoesNotExist:
            messages.error(request, "Current user is not a Guard Office user.")
            return redirect(reverse('add_guard_bulk'))

        for index, row in enumerate(csv_data):
            try:
                first_name = row.get('first_name', 'Default')
                last_name = row.get('last_name', 'Default')
                
                # Check if first name and last name are characters only
                if not first_name.isalpha() or not last_name.isalpha():
                    messages.warning(request, f"Invalid first name or last name in row {index + 1}. Skipping this entry.")
                    print(f"Skipping row {index + 1}: Invalid first name or last name")
                    continue

                email = row.get('email')
                gender = gender_map.get(row.get('gender', '').lower(), 'M')  # Map gender to 'M' or 'F'
                address = row.get('address', '')
                password = '123'  # Default password

                if not email:
                    print(f"Skipping row {index + 1}: Email is missing")
                    continue

                # Check for duplicate email
                if CustomUser.objects.filter(email=email).exists():
                    messages.warning(request, f"Duplicate email found: {email}. Skipping this entry.")
                    print(f"Skipping row {index + 1}: Duplicate email {email}")
                    continue

                # Assign guardofficeuser's guard_office
                guard_office = guardofficeuser_guard_office
                site = None

                print(f"Row {index + 1}: Assigning guardofficeuser's guard_office '{guard_office}' to guard with email {email}")

                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    address=address,
                    user_type='3',  
                    profile_pic=None  # Default to None as in bulk upload process
                )

                print(f"Row {index + 1}: guard_office before creating Employee: {guard_office}")
                Guard.objects.create(
                    admin=user,
                    guard_office=guard_office,
                    site=site  # Ensure site is set to None
                )
                print(f"Row {index + 1}: Employee created with email {email}, guard_office {guard_office}, site {site}")

            except Exception as e:
                messages.error(request, f"Error adding guard with email {email}: {e}")
                print(f"Error processing row {index + 1} with email {email}: {e}")

            # Break the loop if it is the last row
            if index == total_rows - 1:
                break

        messages.success(request, 'Employees added successfully.')
        return redirect(reverse('guardofficeuser_manage_guard'))

    return render(request, 'guardofficeuser_template/add_guard_bulk.html', {'page_title': 'Add Guards in Bulk'})

@csrf_exempt
def view_guard_leave(request):
    if request.method != 'POST':
        guardofficeuser = get_object_or_404(GuardOfficeUser, admin=request.user)
        guards = Guard.objects.filter(guard_office=guardofficeuser.guard_office)
        allLeave = LeaveReportGuard.objects.filter(guard__in=guards)
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Employees'
        }
        return render(request, "guardofficeuser_template/guard_leave_view.html", context)
    else:
        try:
            id = request.POST.get('id')
            status = request.POST.get('status')
            if status == '1':
                status = 1
            else:
                status = -1
            leave = get_object_or_404(LeaveReportGuard, id=id)
            leave.status = status
            leave.save()

            # Send email notification to the guard
            guard = leave.guard
            subject = 'Leave Request Status'
            message = f'Your leave request for {leave.date} has been {leave.get_status_display()}.'
            from_email = os.environ.get('EMAIL_ADDRESS') 
            to_email = guard.admin.email
            send_mail(subject, message, from_email, [to_email])

            # Send email notification to all clients associated with the guard's site
            clients = Client.objects.filter(site=guard.site)
            for client in clients:
                client_email = client.admin.email
                client_message = f'The leave request for guard {guard.admin.get_full_name()} for {leave.date} has been {leave.get_status_display()}.'
                send_mail(subject, client_message, from_email, [client_email])

            return HttpResponse(True)
        except Exception as e:
            print(e)
            # Log the exception or handle it accordingly
            return HttpResponse(False)  # or return an appropriate response

        
def add_site(request):
    form = SiteForm(request.POST or None)
    guard_office = None

    try:
        guard_office_user = GuardOfficeUser.objects.get(admin=request.user)
        guard_office = guard_office_user.guard_office
    except GuardOfficeUser.DoesNotExist:
        messages.error(request, "User does not have an associated guard office")
        return redirect('add_site') 

    if request.method == 'POST':
        form_data = request.POST.copy()
        form_data['guard_office'] = guard_office.id  # Set the guard_office ID in the form data

        form = SiteForm(form_data)

        if form.is_valid():
            radius = form.cleaned_data['radius']
            if radius > MAX_RADIUS:
                messages.error(request, f'Radius cannot be greater than {MAX_RADIUS} meters.')
            else:
                site = form.save(commit=False)
                site.guard_office = guard_office  # Set the guard_office to the user's guard_office
                site.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('manage_site'))
        else:
            messages.error(request, "Fill Form Properly")
    else:
        form.fields['guard_office'].initial = guard_office.id
        form.fields['guard_office'].widget.attrs['readonly'] = True
        form.fields['guard_office'].widget.attrs['disabled'] = True

    context = {
        'form': form,
        'page_title': 'Add Site',
        'guard_office': guard_office,
        'max_radius': MAX_RADIUS
    }

    return render(request, 'guardofficeuser_template/add_site_template.html', context)

def view_site_location(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    context = {
        'site': site,
        'page_title': 'View Site Location'
    }
    return render(request, 'guardofficeuser_template/view_site_location.html', context)


def manage_site(request):
    guardofficeuser = get_object_or_404(GuardOfficeUser, admin=request.user)
    sites = Site.objects.filter(guard_office=guardofficeuser.guard_office)

    for site in sites:
        site.total_guards = Guard.objects.filter(site=site).count()

    unassigned_guards_count = Guard.objects.filter(site__isnull=True, guard_office=guardofficeuser.guard_office).count()

    context = {
        'sites': sites,
        'unassigned_guards_count': unassigned_guards_count,
        'page_title': 'Manage Sites'
    }
    return render(request, "guardofficeuser_template/manage_site.html", context)

from django import forms

def edit_site(request, site_id):
    instance = get_object_or_404(Site, id=site_id)

    try:
        guard_office_user = GuardOfficeUser.objects.get(admin=request.user)
        guard_office = guard_office_user.guard_office
    except GuardOfficeUser.DoesNotExist:
        messages.error(request, "User does not have an associated guard office")
        return redirect('some_error_page')

    form = SiteForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully Updated")
            return redirect(reverse('manage_site'))
        else:
            messages.error(request, "Fill Form Properly")

    context = {
        'form': form,
        'site_id': site_id,
        'page_title': 'Edit Site',
        'max_radius': MAX_RADIUS 
    }

    return render(request, 'guardofficeuser_template/edit_site_template.html', context)


def delete_site(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    site.delete()
    messages.success(request, "Site deleted successfully!")
    return redirect(reverse('manage_site'))

def guard_locations(request):
    context = {
        'page_title': 'Guard Locations'
    }
    return render(request, 'guardofficeuser_template/guard_locations.html', context)