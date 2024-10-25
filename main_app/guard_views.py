import json
import math
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .forms import *
from .models import *
from django.shortcuts import render, get_object_or_404
import math
from django.core.mail import send_mail
from django.utils import timezone
import os 

def guard_home(request):
    guard = get_object_or_404(Guard, admin=request.user)
    total_site = Site.objects.filter(guard_office=guard.guard_office).count()
    total_attendance = AttendanceReport.objects.filter(guard=guard).count()
    total_present = AttendanceReport.objects.filter(guard=guard, status=True).count()
    
    if total_attendance == 0:  # Avoid division by zero
        percent_absent = percent_present = 0
    else:
        percent_present = math.floor((total_present / total_attendance) * 100)
        percent_absent = math.ceil(100 - percent_present)
    
    site_name = []
    data_present = []
    data_absent = []
    sites = Site.objects.filter(guard_office=guard.guard_office)
    
    for site in sites:
        attendance = Attendance.objects.filter(site=site)
        present_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=True, guard=guard).count()
        absent_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=False, guard=guard).count()
        site_name.append(site.name)
        data_present.append(present_count)
        data_absent.append(absent_count)
    
    site_name_value = guard.site.name if guard.site else 'Not Assigned'

    context = {
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'total_site': total_site,
        'sites': sites,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': site_name,
        'page_title': 'Guard Homepage - ' + request.user.get_full_name(),
        'sitename': site_name_value,
    }
    
    return render(request, 'guard_template/home_content.html', context)


@ csrf_exempt
def guard_view_attendance(request):
    guard = get_object_or_404(Guard, admin=request.user)
    if request.method != 'POST':
        guard_office = get_object_or_404(GuardOffice, id=guard.guard_office.id)
        context = {
            'sites': Site.objects.filter(guard_office=guard_office),
            'page_title': 'View Attendance'
        }
        return render(request, 'guard_template/guard_view_attendance.html', context)
    else:
        site_id = request.POST.get('site')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        try:
            site = get_object_or_404(Site, id=site_id)
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            attendance = Attendance.objects.filter(
                date__range=(start_date, end_date), site=site)
            attendance_reports = AttendanceReport.objects.filter(
                attendance__in=attendance, guard=guard)
            json_data = []
            for report in attendance_reports:
                data = {
                    "date":  str(report.attendance.date),
                    "status": report.status
                }
                json_data.append(data)
            return JsonResponse(json.dumps(json_data), safe=False)
        except Exception as e:
            return None


def guard_apply_leave(request):
    form = LeaveReportGuardForm(request.POST or None)
    guard = get_object_or_404(Guard, admin_id=request.user.id)
    total_leave_days = guard.individual_leave_days if guard.individual_leave_days is not None else guard.guard_office.total_leave_days
    used_leave_days = LeaveReportGuard.objects.filter(guard=guard, status=1).count()
    remaining_leave_days = total_leave_days - used_leave_days
    
    context = {
        'form': form,
        'leave_history': LeaveReportGuard.objects.filter(guard=guard),
        'page_title': 'Apply for leave',
        'remaining_leave_days': remaining_leave_days
    }
    
    if request.method == 'POST' and 'cancel_leave_id' not in request.POST:
        if remaining_leave_days <= 0:
            messages.error(request, "You have exhausted your leave days for this period.")
        elif form.is_valid(): 
            try:
                leave_date = form.cleaned_data.get('date')
                existing_leave = LeaveReportGuard.objects.filter(guard=guard, date=leave_date)
                if existing_leave.exists():
                    status_set = set(existing_leave.values_list('status', flat=True))
                    if 0 in status_set:  # Check if there are pending leaves
                        messages.error(request, "Leave Request for this Date is still Pending")
                    else:
                        status_text = [dict(LeaveReportGuard.STATUS_CHOICES).get(status, "Unknown") for status in status_set]
                        messages.error(request, f"Leave for this date has already been {', '.join(status_text)}")
                else:
                    obj = form.save(commit=False)
                    obj.guard = guard
                    obj.save()

                    # Send email notification to the GuardOfficeUsers
                    guard_office_users = GuardOfficeUser.objects.filter(guard_office=guard.guard_office)
                    
                    subject = 'New Leave Request'
                    message = f'A new leave request has been submitted by {guard.admin.first_name} from {guard.site.name} for the date {obj.date}.'
                    from_email = settings.EMAIL_HOST_USER

                    for guard_office_user in guard_office_users:
                        to_email = guard_office_user.admin.email
                        send_mail(subject, message, from_email, [to_email])

                    # Send email notification to the Client
                    try:
                        client = Client.objects.get(site=guard.site)
                        client_email = client.admin.email
                        send_mail(subject, message, from_email, [client_email])
                    except Client.DoesNotExist:
                        messages.warning(request, "No client assigned.")
                    
                    messages.success(request, "Application for leave has been submitted for review")
                    return redirect(reverse('guard_apply_leave'))
            except Exception as e:
                messages.error(request, "Could not submit: " + str(e))
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(error)
            messages.error(request, "Form has errors! " + ' '.join(error_messages))
    return render(request, "guard_template/guard_apply_leave.html", context)


def edit_leave_request(request, leave_id):
    guard = get_object_or_404(Guard, admin_id=request.user.id)
    leave_request = get_object_or_404(LeaveReportGuard, id=leave_id, guard=guard)

    if leave_request.status != 0:
        messages.error(request, "Only pending leave requests can be edited.")
        return redirect(reverse('guard_apply_leave'))

    if request.method == 'POST':
        form = LeaveReportGuardForm(request.POST, instance=leave_request)
        if form.is_valid():
            try:
                old_date = leave_request.date
                form.save()
                
                # Send email notification to the GuardOfficeUsers
                guard_office_users = GuardOfficeUser.objects.filter(guard_office=guard.guard_office)
                subject = 'Leave Request Edited'
                message = f'The leave request for date {old_date} has been changed to {leave_request.date} by {guard.admin.first_name} from {guard.site.name}.'
                from_email = settings.EMAIL_HOST_USER

                for guard_office_user in guard_office_users:
                    to_email = guard_office_user.admin.email
                    send_mail(subject, message, from_email, [to_email])
                
                try:
                    client = Client.objects.get(site=guard.site)
                    client_email = client.admin.email
                    send_mail(subject, message, from_email, [client_email])
                except Client.DoesNotExist:
                    messages.warning(request, "No client associated with this site.")
                    
                messages.success(request, "Leave request updated successfully.")
                return redirect(reverse('guard_apply_leave'))
            except Exception as e:
                messages.error(request, "Could not update leave request: " + str(e))
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(error)
            messages.error(request, "Form has errors! " + ' '.join(error_messages))
    else:
        form = LeaveReportGuardForm(instance=leave_request)

    context = {
        'form': form,
        'page_title': 'Edit Leave Request'
    }
    return render(request, "guard_template/edit_leave_request.html", context)


def cancel_leave_request(request):
    if request.method == 'POST' and 'cancel_leave_id' in request.POST:
        leave_id = request.POST.get('cancel_leave_id')
        guard = get_object_or_404(Guard, admin_id=request.user.id)
        leave_report = get_object_or_404(LeaveReportGuard, id=leave_id, guard=guard)
        if leave_report.status == 0:  # Pending status
            leave_date = leave_report.date
            leave_report.delete()

            # Send email notification to the GuardOfficeUsers
            guard_office_users = GuardOfficeUser.objects.filter(guard_office=guard.guard_office)
            subject = 'Leave Request Cancelled'
            message = f'The leave request submitted by {guard.admin.first_name} from {guard.site.name} for the date {leave_date} has been cancelled.'
            from_email = settings.EMAIL_HOST_USER

            for guard_office_user in guard_office_users:
                to_email = guard_office_user.admin.email
                send_mail(subject, message, from_email, [to_email])
            try:
                client = Client.objects.get(site=guard.site)
                client_email = client.admin.email
                send_mail(subject, message, from_email, [client_email])
            except Client.DoesNotExist:
                messages.warning(request, "No client associated with this site.")
            messages.success(request, "Leave request cancelled successfully.")
        else:
            messages.error(request, "Only pending leave requests can be cancelled.")
    return redirect(reverse('guard_apply_leave'))

# def delete_leave_request(request):
#     if request.method == 'POST':
#         form = DeleteLeaveForm(request.POST, user=request.user)
#         if form.is_valid():
#             form.cleaned_data['leave_requests'].delete()
#             messages.success(request, "Selected leave requests have been deleted.")
#             return redirect('guard_delete_leave')
#     else:
#         form = DeleteLeaveForm(user=request.user)

#     context = {
#         'form': form,
#         'page_title': 'Delete Leave Requests'
#     }
#     return render(request, 'guard_template/guard_delete_leave.html', context)

def guard_feedback(request):
    form = FeedbackGuardForm(request.POST or None)
    guard = get_object_or_404(Guard, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackGuard.objects.filter(guard=guard),
        'page_title': 'Application Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.guard = guard
                obj.save()

                # Retrieve all admin emails
                try:
                    admins = CustomUser.objects.filter(user_type=1)
                    admin_emails = [admin.email for admin in admins]

                    # Send email notification to all admins
                    subject = f"New feedback submitted by {guard.admin.get_full_name()}"
                    message = f"Hello Admin,\n\nNew feedback has been submitted by Guard {guard.admin.get_full_name()}.\n\nFeedback: {obj.feedback}\n\nBest regards,\nSmartPatrol"
                    from_email = os.environ.get('EMAIL_ADDRESS')
                    send_mail(subject, message, from_email, admin_emails)

                    messages.success(request, "Feedback submitted for review")
                except Exception as e:
                    print(f"Error sending email: {str(e)}")  # Log the error for debugging
                    messages.error(request, "Feedback submitted but email could not be sent!")

                return redirect(reverse('guard_feedback'))
            except Exception as e:
                print(f"Error saving feedback: {str(e)}")  # Log the error for debugging
                messages.error(request, "Could not submit feedback!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "guard_template/guard_feedback.html", context)


def guard_view_profile(request):
    guard = get_object_or_404(Guard, admin=request.user)
    form = GuardEditForm(request.POST or None, request.FILES or None,
                           instance=guard)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = guard.admin
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
                guard.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('guard_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, "Error Occured While Updating Profile " + str(e))

    return render(request, "guard_template/guard_view_profile.html", context)


@csrf_exempt
def guard_fcmtoken(request):
    token = request.POST.get('token')
    guard_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        guard_user.fcm_token = token
        guard_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def guard_view_notification(request):
    guard = get_object_or_404(Guard, admin=request.user)
    notifications = NotificationGuard.objects.filter(guard=guard)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "guard_template/guard_view_notification.html", context)


def guard_view_salary(request):
    guard = get_object_or_404(Guard, admin=request.user)
    salarys = GuardSalary.objects.filter(guard=guard)
    total_salary = salarys.aggregate(total_base=models.Sum('base'))['total_base'] or 0  # Calculate total base salary
    context = {
        'salarys': salarys,
        'total_salary': total_salary,
        'page_title': "View Salary"
    }
    return render(request, "guard_template/guard_view_salary.html", context)

@csrf_exempt
def check_in(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        guard_email = data.get('guard_email')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        action = data.get('action')

        try:
            guard = Guard.objects.get(admin__email=guard_email)
            site = guard.site
            if not site:
                return JsonResponse({'success': False, 'message': 'Guard is not assigned to any site'}, status=400)

            site_latitude = site.latitude
            site_longitude = site.longitude
            radius = site.radius 

            distance = haversine(latitude, longitude, site_latitude, site_longitude)

            if action == 'update':
                if guard.is_checked_in:
                    GuardLocation.objects.update_or_create(
                        guard=guard,
                        defaults={'latitude': latitude, 'longitude': longitude, 'timestamp': timezone.now()}
                    )
                    return JsonResponse({'success': True, 'message': 'Location updated'})
                else:
                    return JsonResponse({'success': False, 'message': 'Guard is not checked in'}, status=400)

            if distance <= radius:
                if action == 'checkin':
                    GuardLocation.objects.update_or_create(
                        guard=guard,
                        defaults={'latitude': latitude, 'longitude': longitude, 'timestamp': timezone.now()}
                    )
                    guard.is_checked_in = True
                    guard.is_checked_out = False
                    guard.save()

                    # Create a new attendance log
                    AttendanceLog.objects.create(
                        guard=guard,
                        check_in_time=timezone.now()
                    )

                    return JsonResponse({'success': True, 'message': 'Check-in successful', 'action': 'checkin'})
                elif action == 'checkout':
                    guard.is_checked_in = False
                    guard.is_checked_out = True
                    guard.save()

                    # Update the attendance log with check-out time and duration
                    attendance_log = AttendanceLog.objects.filter(guard=guard, check_out_time__isnull=True).last()
                    if attendance_log:
                        attendance_log.check_out_time = timezone.now()
                        attendance_log.duration = attendance_log.check_out_time - attendance_log.check_in_time
                        attendance_log.save()

                    return JsonResponse({'success': True, 'message': 'Check-out successful', 'action': 'checkout'})
            else:
                return JsonResponse({'success': False, 'message': 'You are not within the allowed radius. Check-in not allowed.'})
        except Guard.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Guard not found'}, status=404)
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

def guard_status(request, email):
    try:
        guard = Guard.objects.get(admin__email=email)
        return JsonResponse({'is_checked_in': guard.is_checked_in, 'is_checked_out': guard.is_checked_out})
    except Guard.DoesNotExist:
        return JsonResponse({'error': 'Guard not found'}, status=404)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3  # Radius of the Earth in meters
    φ1 = radians(lat1)
    φ2 = radians(lat2)
    Δφ = radians(lat2 - lat1)
    Δλ = radians(lon2 - lon1)

    a = sin(Δφ / 2) * sin(Δφ / 2) + cos(φ1) * cos(φ2) * sin(Δλ / 2) * sin(Δλ / 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c  # Distance in meters

def guard_checkin_page(request):
    guard_email = request.user.email
    try:
        guard = Guard.objects.get(admin__email=guard_email)
        site = guard.site
        site_latitude = site.latitude if site else None
        site_longitude = site.longitude if site else None
        site_radius = site.radius if site else None

    except Guard.DoesNotExist:
        site_latitude = None
        site_longitude = None
        site_radius = None
       

    context = {
        'page_title': 'Guard Check-in/out',
        'site_latitude': site_latitude,
        'site_longitude': site_longitude,
        'site_radius': site_radius
    }
    return render(request, 'guard_template/guard_checkin.html', context)

def guard_status(request, email):
    try:
        guard = Guard.objects.get(admin__email=email)
        return JsonResponse({'is_checked_in': guard.is_checked_in})
    except Guard.DoesNotExist:
        return JsonResponse({'error': 'Guard not found'}, status=404)
    
