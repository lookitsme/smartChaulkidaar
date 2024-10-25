from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .EmailBackend import EmailBackend
from .models import *
from django.db.models import Q
from .forms import ReviewForm, FeedbackClientForm
from django.contrib import messages
from django.core.mail import send_mail
import os

def client_home(request):
    try:
        client = Client.objects.get(admin=request.user)
    except Client.DoesNotExist:
        return render(request, 'client_template/home_content.html', {'message': 'Client not found'})

    client_sites = Site.objects.filter(client=client)
    total_guards_assigned = Guard.objects.filter(site__in=client_sites).count()

    today = timezone.now().date()
    guards_on_leave_today = LeaveReportGuard.objects.filter(
        guard__site__in=client_sites, date=today, status=1).count()

    site_list = []
    guards_assigned_list = []
    for site in client_sites:
        guards_assigned_count = Guard.objects.filter(site=site).count()
        site_list.append(site.name[:7])
        guards_assigned_list.append(guards_assigned_count)

    context = {
        'page_title': "Client Dashboard - SmartPatrol",
        'total_guards_assigned': total_guards_assigned,
        'guards_on_leave_today': guards_on_leave_today,
        'site_list': site_list,
        'guards_assigned_list': guards_assigned_list
    }

    return render(request, 'client_template/home_content.html', context)

def view_guards_on_leave(request):
    try:
        client = Client.objects.get(admin=request.user)
    except Client.DoesNotExist:
        return render(request, 'client_template/home_content.html', {'message': 'Client not found'})

    client_sites = Site.objects.filter(client=client)
    today = timezone.now().date()
    guards_on_leave_today = LeaveReportGuard.objects.filter(
        guard__site__in=client_sites, date=today, status=1)

    all_leaves = LeaveReportGuard.objects.filter(guard__site__in=client_sites, status=1)

    context = {
        'page_title': "Guards on Leave Today - SmartPatrol",
        'guards_on_leave_today': guards_on_leave_today,
        'all_leaves': all_leaves
    }

    return render(request, 'client_template/view_guards_on_leave.html', context)

def view_client_guards(request):
    try:
        client = Client.objects.get(admin=request.user)
    except Client.DoesNotExist:
        return render(request, 'client_template/home_content.html', {'message': 'Client not found'})

    client_sites = Site.objects.filter(client=client)
    guards = Guard.objects.filter(site__in=client_sites)

    query = request.GET.get('q')
    if query:
        guards = guards.filter(
            Q(admin__first_name__icontains=query) |
            Q(admin__last_name__icontains=query) |
            Q(admin__email__icontains=query) |
            Q(guard_office__name__icontains=query)
        )

    context = {
        'page_title': "Client Guards - SmartPatrol",
        'guards': guards,
        'query': query or ""
    }
    
    return render(request, 'client_template/view_client_guards.html', context)

def ajax_search_guards(request):
    try:
        client = Client.objects.get(admin=request.user)
    except Client.DoesNotExist:
        return JsonResponse({'error': 'Client not found'}, status=404)

    client_sites = Site.objects.filter(client=client)
    guards = Guard.objects.filter(site__in=client_sites)

    query = request.GET.get('q')
    if query:
        guards = guards.filter(
            Q(admin__first_name__icontains=query) |
            Q(admin__last_name__icontains=query) |
            Q(admin__email__icontains=query) |
            Q(guard_office__name__icontains=query)
        )

    guard_data = []
    for guard in guards:
        guard_data.append({
            'full_name': f"{guard.admin.first_name} {guard.admin.last_name}",
            'email': guard.admin.email,
            'guard_office_name': guard.guard_office.name,
            'site_name': guard.site.name
        })

    return JsonResponse({'results': guard_data})


# def submit_complaint(request):
#     if request.method == 'POST':
#         guard_id = request.POST.get('guard_id')
#         description = request.POST.get('description')

#         guard = Guard.objects.get(id=guard_id)
#         client = Client.objects.get(admin=request.user)
#         guard_office_user = guard.guard_office.guardofficeuser_set.first() 

#         complaint = Complaint.objects.create(
#             guard=guard,
#             client=client,
#             description=description
#         )

#         # Create a notification for the guard office user
#         notification = NotificationGOUser.objects.create(
#             guardofficeuser=guard_office_user,
#             message=f"New complaint filed against {guard.admin.email} by {client.admin.email}: {complaint.description}",
#             is_complaint=True
#         )
#         print(f"Notification created: {notification}")

#         return redirect('view_client_guards')


def submit_complaint(request):
    if request.method == 'POST':
        guard_id = request.POST.get('guard_id')
        description = request.POST.get('description')

        guard = get_object_or_404(Guard, id=guard_id)
        client = get_object_or_404(Client, admin=request.user)
        guard_office = guard.guard_office

        complaint = Complaint.objects.create(
            guard=guard,
            client=client,
            description=description
        )

        guard_office_users = GuardOfficeUser.objects.filter(guard_office=guard_office)
        for guard_office_user in guard_office_users:
            NotificationGOUser.objects.create(
                guardofficeuser=guard_office_user,
                message=f"New complaint filed against {guard.admin.email} by {client.admin.email}: {complaint.description}",
                is_complaint=True
            )

        return redirect('view_client_guards')

def submit_review(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            guard = Guard.objects.get(id=form.cleaned_data['guard_id'])
            client = Client.objects.get(admin=request.user)
            rating = int(form.cleaned_data['rating'])
            review_text = form.cleaned_data['review']
            
            # Check if the client has already reviewed this guard
            existing_review = GuardReview.objects.filter(guard=guard, client=client).first()

            if existing_review:
                # Update the existing review
                existing_review.rating = rating
                existing_review.review = review_text
                existing_review.save()
            else:
                # Create a new review
                GuardReview.objects.create(guard=guard, client=client, rating=rating, review=review_text)
            
            # Recalculate the average rating
            reviews = GuardReview.objects.filter(guard=guard)
            total_rating = sum(review.rating for review in reviews)
            guard.review_count = reviews.count()
            guard.average_rating = total_rating / guard.review_count
            guard.save()
            
            return redirect('view_client_guards') 
    else:
        form = ReviewForm()
    return render(request, 'main_app/review_form.html', {'form': form})

def check(request):
    return render(request, 'client_template/check.html')

def client_feedback(request):
    form = FeedbackClientForm(request.POST or None)
    client = get_object_or_404(Client, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackClient.objects.filter(client=client),
        'page_title': 'Application Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.client = client
                obj.save()

                # Retrieve all admin emails
                try:
                    admins = CustomUser.objects.filter(user_type=1)
                    admin_emails = [admin.email for admin in admins]

                    # Send email notification to all admins
                    subject = f"New feedback submitted by {client.admin.get_full_name()}"
                    message = f"Hello Admin,\n\nNew feedback has been submitted by Client {client.admin.get_full_name()}.\n\nFeedback: {obj.feedback}\n\nBest regards,\nSmartPatrol"
                    from_email = os.environ.get('EMAIL_ADDRESS')
                    send_mail(subject, message, from_email, admin_emails)

                    messages.success(request, "Feedback submitted for review")
                except Exception as e:
                    # print(f"Error sending email: {str(e)}")  
                    messages.error(request, "Feedback submitted but email could not be sent!")

                return redirect(reverse('client_feedback'))
            except Exception as e:
                # print(f"Error saving feedback: {str(e)}")
                messages.error(request, "Could not submit feedback!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "client_template/client_feedback.html", context)

def guard_logs(request):
    if request.user.user_type == '4':  # Assuming '4' is for clients
        client = get_object_or_404(Client, admin=request.user)
        logs = AttendanceLog.objects.filter(guard__site=client.site, is_approved=False)
        context = {
            'logs': logs,
            'page_title': 'Guard Logs'
        }
        return render(request, 'client_template/guard_logs.html', context)
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
@csrf_exempt
def approve_attendance_log(request, log_id):
    if request.method == 'POST' and request.user.is_authenticated and request.user.user_type == '4':
        log = get_object_or_404(AttendanceLog, id=log_id)
        client = get_object_or_404(Client, admin=request.user)

        if log.guard.site == client.site:
            if log.check_out_time is None:
                return JsonResponse({'success': False, 'message': 'Guard has not checked out yet.'})

            log.is_approved = True
            log.save()

            # Ensure an attendance record exists for the log date
            attendance, created = Attendance.objects.get_or_create(
                site=log.guard.site,
                date=log.check_in_time.date(),
                defaults={'created_at': timezone.now()}
            )

            # Get or create an attendance report for the guard
            attendance_report, created = AttendanceReport.objects.get_or_create(
                guard=log.guard,
                attendance=attendance
            )

            # Sum the duration for the current log
            if log.duration:
                attendance_report.duration += log.duration

            attendance_report.status = True
            attendance_report.save()

            return JsonResponse({'success': True, 'message': 'Attendance log approved and valid attendance created.'})
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=401)