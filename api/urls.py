from django.urls import path
from .views import *
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    
    # path('login/', obtain_auth_token, name='register'),
    path('getRoutes/', getRoutes, name='get_routes'),
    path('api/create-user/', CustomUserCreate.as_view(), name='create_user'),
    path('api/update-user/<str:email>/', CustomUserDetail.as_view(), name='update-user-details'),
    path('api/users-all/', CustomUserList.as_view(), name='users_list'),
    
    path('api/managers-all/', ManagerList.as_view(), name='manager_list'),
    path('api/employees-all/', EmployeeList.as_view(), name='employee_list'),
    
    path('api/guardoffice/', guardoffice, name='guardoffice_name'),
    path('api/guardoffice-delete/<str:name>/', guardoffice, name='guardoffice_name_delete'),
    path('api/guardoffice-rename/<str:name>/', guardoffice, name='guardoffice_name_rename'),
    
    path('api/department/', department_detail, name='department-detail'),
    path('api/department-rename/<str:name>/', department_detail, name='department-rename'),
    path('api/department-delete/<str:name>/', department_detail, name='department-delete'),
    
    #Get attendance of a specific user
    #Get attendance of all user in a guardoffice
    #Get attendance of all user in a department
    #public/private endpoints?
    
    
    path('api/login/', APILoginView.as_view(), name='api_login'),
    path('api/logout/', APILogoutView.as_view(), name='api_logout'),
    
    path('api/guard/home/', GuardHomeView.as_view(), name='api_guard_home'),
    path('api/guard/view-attendance/', GuardViewAttendance.as_view(), name='api_guard_view_attendance'),
    path('api/guard/apply-leave/', GuardApplyLeave.as_view(), name='api_guard_apply_leave'),
    path('api/guard/cancel-leave/', CancelLeaveRequest.as_view(), name='api_guard_cancel_leave'),
    path('api/guard/salary/', GuardViewSalary.as_view(), name='api_guard_salary'),
    path('api/guard/feedback/', GuardFeedback.as_view(), name='api_guard_feedback'),
    path('api/guard/profile/', GuardViewProfile.as_view(), name='api_guard_profile'),
    path('api/guard/view-notification/', GuardViewNotification.as_view(), name='api_guard_view_notification'),
    
    path('update_location/', update_location, name='update_location'),
    path('guard_locations/', get_guard_locations, name='get_guard_locations'),
    
]