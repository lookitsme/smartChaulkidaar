"""office_ops URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include

from schema_graph.views import Schema

from main_app.EditSalaryView import EditSalaryView

from . import ceo_views, guard_views, guardofficeuser_views, views, client_views

urlpatterns = [
    path("", views.login_page, name='login_page'),
    path("home_page/", views.home_page, name='home_page'),

    path('search_filter/', views.unified_search_filter, name='unified_search_filter'),
    
    path("get_attendance", views.get_attendance, name='get_attendance'),
    path("firebase-messaging-sw.js", views.showFirebaseJS, name='showFirebaseJS'),
    path("doLogin/", views.doLogin, name='user_login'),
    path("logout_user/", views.logout_user, name='user_logout'),
    path("admin/home/", ceo_views.admin_home, name='admin_home'),
    path("guardofficeuser/add", ceo_views.add_guardofficeuser, name='add_guardofficeuser'),
    path("guard_office/add", ceo_views.add_guard_office, name='add_guard_office'),
    path("send_guard_notification/", ceo_views.send_guard_notification,
         name='send_guard_notification'),
    path("send_guardofficeuser_notification/", ceo_views.send_guardofficeuser_notification,
         name='send_guardofficeuser_notification'),
    path("admin_notify_guard", ceo_views.admin_notify_guard,
         name='admin_notify_guard'),
    path("admin_notify_guardofficeuser", ceo_views.admin_notify_guardofficeuser,
         name='admin_notify_guardofficeuser'),
    path("admin_view_profile", ceo_views.admin_view_profile,
         name='admin_view_profile'),
    path('check-email/', ceo_views.check_email_availability, name='check_email_availability'),
    path("guard/view/feedback/", ceo_views.guard_feedback_message,
         name="guard_feedback_message",),
    path("guardofficeuser/view/feedback/", ceo_views.guardofficeuser_feedback_message,
         name="guardofficeuser_feedback_message",),
    path("client/view/feedback/", ceo_views.client_feedback_message,
         name="client_feedback_message",),
#     path("guard/view/leave/", ceo_views.view_guard_leave,
#          name="view_guard_leave",),
    path("guardofficeuser/view/leave/", ceo_views.view_guardofficeuser_leave, name="view_guardofficeuser_leave",),
    path("attendance/view/", ceo_views.admin_view_attendance,
         name="admin_view_attendance",),
    path("attendance/fetch/", ceo_views.get_admin_attendance,
         name='get_admin_attendance'),
    path("guard/add/", ceo_views.add_guard, name='add_guard'),
    path("guard/add/bulk", ceo_views.add_guard_bulk, name='add_guard_bulk'),
    
    path("admin/site/add/", ceo_views.add_site, name='admin_add_site'),
    path("admin/site/manage/", ceo_views.manage_site, name='admin_manage_site'),
    path("admin/site/edit/<int:site_id>",
         ceo_views.edit_site, name='admin_edit_site'),
    path("admin/site/delete/<int:site_id>",
         ceo_views.delete_site, name='admin_delete_site'),
    
    path("guardofficeuser/manage/", ceo_views.manage_guardofficeuser, name='manage_guardofficeuser'),
    path("guard/manage/", ceo_views.manage_guard, name='manage_guard'),
    path("guard_office/manage/", ceo_views.manage_guard_office, name='manage_guard_office'),
    path("site/manage/", ceo_views.manage_site, name='manage_site'),
    path("guardofficeuser/edit/<int:guardofficeuser_id>", ceo_views.edit_guardofficeuser, name='edit_guardofficeuser'),
    path("guardofficeuser/delete/<int:guardofficeuser_id>",
         ceo_views.delete_guardofficeuser, name='delete_guardofficeuser'),

    path("guard_office/delete/<int:guard_office_id>",
         ceo_views.delete_guard_office, name='delete_guard_office'),

    path("site/delete/<int:site_id>",
         ceo_views.delete_site, name='delete_site'),

    path("guard/delete/<int:guard_id>",
         ceo_views.delete_guard, name='delete_guard'),
    path("guard/edit/<int:guard_id>",
         ceo_views.edit_guard, name='edit_guard'),
    path("guard_office/edit/<int:guard_office_id>",
         ceo_views.edit_guard_office, name='edit_guard_office'),
    path("site/edit/<int:site_id>",
         ceo_views.edit_site, name='edit_site'),
    path("maps/", ceo_views.view_guard_location, name='view_guard_location'),
    
    path("ceo/client/add/", ceo_views.ceo_add_client, name='ceo_add_client'),
    path("ceo/client/manage/", ceo_views.ceo_manage_client, name='ceo_manage_client'),
    path("ceo/client/edit/<int:client_id>", ceo_views.ceo_edit_client, name='ceo_edit_client'),
    path("ceo/client/delete/<int:client_id>",
         ceo_views.ceo_delete_client, name='ceo_delete_client'),
    


    # Guard Office User
    path("guardofficeuser/home/", guardofficeuser_views.guardofficeuser_home, name='guardofficeuser_home'),
#     path("guardofficeuser/apply/leave/", guardofficeuser_views.guardofficeuser_apply_leave,
#          name='guardofficeuser_apply_leave'),
    path("guardofficeuser/feedback/", guardofficeuser_views.guardofficeuser_feedback, name='guardofficeuser_feedback'),
    path("guardofficeuser/view/profile/", guardofficeuser_views.guardofficeuser_view_profile,
         name='guardofficeuser_view_profile'),
    path("guardofficeuser/guard/add/", guardofficeuser_views.add_guard, name='guardofficeuser_add_guard'),
    path("guardofficeuser/guard/manage/", guardofficeuser_views.manage_guard, name='guardofficeuser_manage_guard'),
    path("guardofficeuser/guard/edit/<int:guard_id>", guardofficeuser_views.edit_guard, name='guardofficeuser_edit_guard'),
    path("guardofficeuser/guard/delete/<int:guard_id>",
         guardofficeuser_views.delete_guard, name='guardofficeuser_delete_guard'),
    path("guardofficeuser/attendance/take/", guardofficeuser_views.guardofficeuser_take_attendance,
         name='guardofficeuser_take_attendance'),
    path("guardofficeuser/attendance/update/page", guardofficeuser_views.guardofficeuser_update_attendance,
         name='guardofficeuser_update_attendance'),
    path("guardofficeuser/get_guards/", guardofficeuser_views.get_guards, name='get_guards'),
    path("guardofficeuser/attendance/fetch/", guardofficeuser_views.get_guard_attendance,
         name='get_guard_attendance'),
    path("guardofficeuser/attendance/save/",
         guardofficeuser_views.save_attendance, name='save_attendance'),
    path("guardofficeuser/attendance/update/",
         guardofficeuser_views.update_attendance, name='update_attendance'),
    path("guardofficeuser/fcmtoken/", guardofficeuser_views.guardofficeuser_fcmtoken, name='guardofficeuser_fcmtoken'),
    path("guardofficeuser/view/notification/", guardofficeuser_views.guardofficeuser_view_notification,
         name="guardofficeuser_view_notification"),
    path("guardofficeuser/salary/add/", guardofficeuser_views.guardofficeuser_add_salary, name='guardofficeuser_add_salary'),
    path("guardofficeuser/salary/edit/", EditSalaryView.as_view(),
         name='edit_guard_salary'),
    path('guardofficeuser/salary/fetch/', guardofficeuser_views.fetch_guard_salary,
         name='fetch_guard_salary'),
    path("guards/add/bulk", guardofficeuser_views.add_guard_bulk, name='add_guard_bulk'),
    path("guard/view/leave/", guardofficeuser_views.view_guard_leave,
         name="view_guard_leave",),
      
    path("guardofficeuser/client/add/", guardofficeuser_views.add_client, name='guardofficeuser_add_client'),
    path("guardofficeuser/client/manage/", guardofficeuser_views.manage_client, name='guardofficeuser_manage_client'),
    path("guardofficeuser/client/edit/<int:client_id>/", guardofficeuser_views.edit_client, name='guardofficeuser_edit_client'),
    path("guardofficeuser/client/delete/<int:client_id>/", guardofficeuser_views.delete_client, name='guardofficeuser_delete_client'),
    
    path('check_email/', guardofficeuser_views.check_email_availability, name="check_email_availability"),
    path("guardofficeuser/site/add/", guardofficeuser_views.add_site, name='add_site'),
    path("guardofficeuser/site/manage/", guardofficeuser_views.manage_site, name='manage_site'),
    path("guardofficeuser/site/edit/<int:site_id>",
         guardofficeuser_views.edit_site, name='edit_site'),
    path("guardofficeuser/site/delete/<int:site_id>",
         guardofficeuser_views.delete_site, name='delete_site'),
    path('guardofficeuser/site/view_location/<int:site_id>/', guardofficeuser_views.view_site_location, name='view_site_location'),
#     path('guard_office/update_leave_days/', guardofficeuser_views.update_guard_office_leave_days, name='update_guard_office_leave_days'),
#     path('guard/update_leave_days/', guardofficeuser_views.update_guard_leave_days, name='update_guard_leave_days'),
    path('guard_locations/', guardofficeuser_views.guard_locations, name='guard_locations'),
    path('assign_guards_to_site/', guardofficeuser_views.assign_guards_to_site, name='assign_guards_to_site'),
    
    
    # Guard
    path("guard/home/", guard_views.guard_home, name='guard_home'),
    path("guard/view/attendance/", guard_views.guard_view_attendance,
         name='guard_view_attendance'),
    path("guard/apply/leave/", guard_views.guard_apply_leave,
         name='guard_apply_leave'),
    path('guard/cancel/leave/', guard_views.cancel_leave_request, name='cancel_leave_request'),
     path('guard/edit-leave/<int:leave_id>/', guard_views.edit_leave_request, name='edit_leave_request'),
    path("guard/feedback/", guard_views.guard_feedback,
         name='guard_feedback'),
    path("guard/view/profile/", guard_views.guard_view_profile,
         name='guard_view_profile'),
    path("guard/fcmtoken/", guard_views.guard_fcmtoken,
         name='guard_fcmtoken'),
    path("guard/view/notification/", guard_views.guard_view_notification,
         name="guard_view_notification"),
    path('guard/view/salary/', guard_views.guard_view_salary,
         name='guard_view_salary'),
    path('guard/check_in/', guard_views.check_in, name='check_in'),
    
    path('guard/checkin/', guard_views.guard_checkin_page, name='guard_checkin_page'),
    
    path('guard_status/<str:email>/', guard_views.guard_status, name='guard_status'),
     # path('guard/delete_leave/', guard_views.delete_leave_request, name='guard_delete_leave'),
     path("schema/", Schema.as_view()),
      
      
      
     # Client 
     path("client/home/", client_views.client_home, name='client_home'),
     path('client/guards/', client_views.view_client_guards, name='view_client_guards'),
     path('client/guards/on_leave/', client_views.view_guards_on_leave, name='view_guards_on_leave'),
     path('client/guards/ajax_search/', client_views.ajax_search_guards, name='ajax_search_guards'),
     path('client/guards/submit_complaint/', client_views.submit_complaint, name='submit_complaint'),
     path('client/submit_review/', client_views.submit_review, name='submit_review'),
     path("check/", client_views.check, name="check"),
     path("client/feedback/", client_views.client_feedback, name='client_feedback'),
     path('fetch_notifications/', views.fetch_notifications, name='fetch_notifications'),
     path('view_all_notifications/', views.view_all_notifications, name='view_all_notifications'),
     path('clear_notifications/', views.clear_notifications, name='clear_notifications'),
     
     path('api/', include('api.urls')), 
     
     path('view_guard_logs/', client_views.guard_logs, name='view_guard_logs'),
     path('approve_attendance_log/<int:log_id>/', client_views.approve_attendance_log, name='approve_attendance_log'),
     
     path('guard/profile/<int:guard_id>/', views.view_guard_profile, name='view_guard_profile'),
    
]
