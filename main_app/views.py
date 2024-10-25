import json
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .EmailBackend import EmailBackend
from .models import *
from django.db.models import Q

# Create your views here.

def home_page(request):
    return render(request, 'main_app/home.html')

def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("guardofficeuser_home"))
        elif request.user.user_type == '3':
            return redirect(reverse("guard_home"))
        elif request.user.user_type == '4':
            return redirect(reverse("client_home"))
        else:
            return redirect("/")
    return render(request, 'main_app/login.html')


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:
        # # Google recaptcha
        # captcha_token = request.POST.get('g-recaptcha-response')
        # captcha_url = "https://www.google.com/recaptcha/api/siteverify"
        # captcha_key = "6Lf9RfcnAAAAAIn2o_U8h3KQwb3lVMeDvenBCXYp"
        # data = {
        #     'secret': captcha_key,
        #     'response': captcha_token
        # }
        # # Make request
        # try:
        #     captcha_server = requests.post(url=captcha_url, data=data)
        #     response = json.loads(captcha_server.text)
        #     if response['success'] == False:
        #         messages.error(request, 'Invalid Captcha. Try Again')
        #         return redirect('/')
        # except:
        #     messages.error(request, 'Captcha could not be verified. Try Again')
        #     return redirect('/')
        
        # Authenticate
        user = authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user is not None:
            login(request, user)
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("guardofficeuser_home"))
            elif request.user.user_type == '3':
                return redirect(reverse("guard_home"))
            elif request.user.user_type == '4':
                return redirect(reverse("client_home"))
            else:
                return redirect("/")
        else:
            messages.error(request, "Invalid details")
            return redirect("/")


def logout_user(request):
    if request.user != None:
        logout(request)
    return redirect("/")


@csrf_exempt
def get_attendance(request):
    site_id = request.POST.get('site')
    try:
        site = get_object_or_404(Site, id=site_id)
        attendance = Attendance.objects.filter(site=site)
        attendance_list = []
        for attd in attendance:
            data = {
                    "id": attd.id,
                    "attendance_date": str(attd.date)
                    }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception as e:
        return None

@login_required
def fetch_notifications(request):
    user = request.user
    notifications_data = []

    if hasattr(user, 'guardofficeuser'):
        guard_office_user = user.guardofficeuser
        notifications = NotificationGOUser.objects.filter(guardofficeuser=guard_office_user).order_by('-created_at')
        for n in notifications:
            notifications_data.append({
                'message': n.message,
                'created_at': n.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
    return JsonResponse({'notifications': notifications_data})

@login_required
def view_all_notifications(request):
    user = request.user

    if hasattr(user, 'guardofficeuser'):
        guard_office_user = user.guardofficeuser
        notifications = NotificationGOUser.objects.filter(guardofficeuser=guard_office_user).order_by('-created_at')
    else:
        notifications = []

    context = {
        'notifications': notifications,
        'page_title': 'All Notifications',
    }
    return render(request, 'main_app/view_all_notifications.html', context)


@login_required
def clear_notifications(request):
    if request.method == 'POST':
        Notification.objects.filter(admin=request.user, is_read=False).update(is_read=True)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})


# @login_required
# def unified_search_filter(request):
#     query = request.GET.get('query', '')
#     site_id = request.GET.get('site', '')
#     gender = request.GET.get('gender', '')
#     user_type = request.GET.get('user_type', '')

#     filters = Q()

#     if user_type == 'guard':
#         guardofficeuser = GuardOfficeUser.objects.get(admin=request.user)
#         filters &= Q(user_type=3) & Q(guard__guard_office=guardofficeuser.guard_office)
#     elif user_type == 'client':
#         filters &= Q(user_type=4)

#     if query:
#         filters &= Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
#     if site_id:
#         filters &= Q(guard__site_id=site_id)
#     if gender:
#         filters &= Q(gender=gender)

#     results = CustomUser.objects.filter(filters)

#     results_list = []
#     for user in results:
#         if user_type == 'guard':
#             results_list.append({
#                 'sn': user.pk,
#                 'full_name': f"{user.last_name}, {user.first_name}",
#                 'email': user.email,
#                 'gender': user.get_gender_display(),
#                 'guard_office': user.guard.guard_office.name if user.guard.guard_office else '',
#                 'site': user.guard.site.name if user.guard.site else '',
#                 'profile_pic': user.profile_pic.url if user.profile_pic else ''
#             })
#         elif user_type == 'client':
#             results_list.append({
#                 'sn': user.pk,
#                 'full_name': f"{user.last_name}, {user.first_name}",
#                 'email': user.email,
#                 'gender': user.get_gender_display(),
#                 'company_name': user.client.company_name if hasattr(user, 'client') else '',
#                 'vat_number': user.client.vat_number if hasattr(user, 'client') else '',
#                 'profile_pic': user.profile_pic.url if user.profile_pic else ''
#             })

#     return JsonResponse(results_list, safe=False)

def unified_search_filter(request):
    query = request.GET.get('query', '')
    site_name = request.GET.get('site', '')
    gender = request.GET.get('gender', '')
    user_type = request.GET.get('user_type', '')

    filters = Q()

    if user_type == 'guard':
        guardofficeuser = GuardOfficeUser.objects.get(admin=request.user)
        filters &= Q(user_type=3) & Q(guard__guard_office=guardofficeuser.guard_office)
    elif user_type == 'client':
        guardofficeuser = GuardOfficeUser.objects.get(admin=request.user)
        filters &= Q(user_type=4) & Q(client__guard_office=guardofficeuser.guard_office)

    if query:
        filters &= (
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query) | 
            Q(client__vat_number__iexact=query)  # Use iexact for exact match on VAT number
        )
    if site_name:
        if user_type == 'guard':
            filters &= Q(guard__site__name__icontains=site_name)
        elif user_type == 'client':
            filters &= Q(client__site__name__icontains=site_name)
    if gender:
        filters &= Q(gender=gender)

    results = CustomUser.objects.filter(filters)

    results_list = []
    for user in results:
        if user_type == 'guard':
            results_list.append({
                'sn': user.pk,
                'full_name': f"{user.last_name}, {user.first_name}",
                'email': user.email,
                'gender': user.get_gender_display(),
                'guard_office': user.guard.guard_office.name if user.guard.guard_office else '',
                'site': user.guard.site.name if user.guard.site else '',
                'profile_pic': user.profile_pic.url if user.profile_pic else ''
            })
        elif user_type == 'client':
            results_list.append({
                'sn': user.pk,
                'full_name': f"{user.last_name}, {user.first_name}",
                'email': user.email,
                'gender': user.get_gender_display(),
                'company_name': user.client.company_name if hasattr(user, 'client') else '',
                'vat_number': user.client.vat_number if hasattr(user, 'client') else '',
                'site': user.client.site.name if hasattr(user, 'client') and user.client.site else '',
                'guard_office': user.client.guard_office.name if hasattr(user, 'client') and user.client.guard_office else '',
                'profile_pic': user.profile_pic.url if user.profile_pic else ''
            })

    return JsonResponse(results_list, safe=False)


def showFirebaseJS(request):
    data = """
    // Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in
// your app's Firebase config object.
// https://firebase.google.com/docs/web/setup#config-object
firebase.initializeApp({
    apiKey: "AIzaSyBarDWWHTfTMSrtc5Lj3Cdw5dEvjAkFwtM",
    authDomain: "sms-with-django.firebaseapp.com",
    databaseURL: "https://sms-with-django.firebaseio.com",
    projectId: "sms-with-django",
    storageBucket: "sms-with-django.appspot.com",
    messagingSenderId: "945324593139",
    appId: "1:945324593139:web:03fa99a8854bbd38420c86",
    measurementId: "G-2F2RXTL9GT"
});

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();
messaging.setBackgroundMessageHandler(function (payload) {
    const notification = JSON.parse(payload);
    const notificationOption = {
        body: notification.body,
        icon: notification.icon
    }
    return self.registration.showNotification(payload.notification.title, notificationOption);
});
    """
    return HttpResponse(data, content_type='application/javascript')

def view_guard_profile(request, guard_id):
    guard = get_object_or_404(Guard, id=guard_id)
    reviews = GuardReview.objects.filter(guard=guard)
    context = {
        'guard': guard,
        'reviews': reviews,
        'page_title': "GuardProfile"
    }
    return render(request, 'main_app/guard_profile.html', context)

