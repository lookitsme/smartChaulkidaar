import math
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from main_app.models import *   
from .serializers import *
from main_app.forms import LeaveReportGuardForm 
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from datetime import datetime
from django.core.mail import send_mail
from django.utils import timezone

@api_view(['GET'])
def getRoutes(request):
    routes =[
        'GET /api/users-all/',
        'PUT /api/create-user/',
        'UPDATE /api/update-user/<str:email>/',
        
        'GET /api/managers-all/',
        'GET /api/employees-all/',
        
        'GET /api/guardoffice/',
        'DELETE /api/guardoffice-delete/<str:name>/',
        'UPDATE /api/guardoffice-rename/<str:name>/',
        
        'GET /api/department/',
        'UPDATE /api/department-rename/<str:name>/',
        'DELETE /api/department-delete/<str:name>/'
        # 'GET /guardofficeName',
        # 'PUT /guardofficeName/add',
    ]
    return Response(routes)


class APILoginView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Please provide both email and password."}, status=status.HTTP_400_BAD_REQUEST)

        print(f"Received email: {email}, password: {password}")

        try:
            user_direct = CustomUser.objects.get(email=email)
            print("User exists directly:", user_direct)
            print("Password check directly:", user_direct.check_password(password))
        except CustomUser.DoesNotExist:
            print("User does not exist directly.")

        user = authenticate(request, username=email, password=password)
        
        if user is None:
            print("Authentication failed.")
            return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        print(f"Authentication successful for user: {user}")

        token, created = Token.objects.get_or_create(user=user)
        
        user_data = CustomUserSerializer(user).data
        return Response({"token": token.key, "user": user_data}, status=status.HTTP_200_OK)

class APILogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        request.user.auth_token.delete()
        logout(request)
        return Response({"success": "Logged out successfully"}, status=status.HTTP_200_OK)


class CustomUserCreate(CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(user__id=response.data['id'])
        return Response({'token': token.key, 'user': response.data}, status=status.HTTP_201_CREATED)

class CustomUserDetail(RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    lookup_field = 'email' 

class CustomUserList(ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

class ManagerList(ListAPIView):
    queryset = CustomUser.objects.filter(user_type=2)
    serializer_class = CustomUserSerializer

class EmployeeList(ListAPIView):
    queryset = CustomUser.objects.filter(user_type=3)
    serializer_class = CustomUserSerializer

@api_view(['GET', 'POST', 'DELETE', 'PUT'])
# @permission_classes([IsAuthenticated])
def guardoffice(request, name=None):
    """
    API endpoint to get guardoffice name, add a guardoffice name, update a guardoffice name, and delete a guardoffice name.

    GET: Returns a list of all guardoffice names.
    POST: Adds a new guardoffice name.
    DELETE: Deletes a guardoffice name.
    PUT: Updates a guardoffice name.

    Usage:
    GET: /guardoffice
    POST: /guardoffice
    DELETE: /guardoffice-delete/<guardoffice_name>
    PUT: /guardoffice-update/<guardoffice_name>

    GET Parameters:
    None

    POST Parameters:
    - name: The name of the guardoffice (required)

    DELETE Parameters:
    - guardoffice_id: The ID of the guardoffice to delete (required)

    PUT Parameters:
    - guardoffice_id: The ID of the guardoffice to update (required)
    - name: The updated name of the guardoffice (required)

    Example Usage:
    GET: /guardoffice
    POST: /guardoffice
        Body: {"name": "New guardoffice"}
    DELETE: /guardoffice-delete/{name}
    PUT: /guardoffice-update/{name}
        Body: {"name": "Updated guardoffice"}

    """
    # if request.user.user_type != 1:
    #     return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        guardoffices = GuardOffice.objects.all()
        serializer = GuardOfficeSerializer(guardoffices, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = GuardOfficeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            guardoffice = GuardOffice.objects.get(name=name)
        except GuardOffice.DoesNotExist:
            return Response({'message': 'guardoffice does not exist'},status=status.HTTP_404_NOT_FOUND)

        serializer = GuardOfficeSerializer(guardoffice, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Updated Sucessfully'}, serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            guardoffice = GuardOffice.objects.get(name=name)
            guardoffice.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except GuardOffice.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)



@api_view(['GET', 'POST', 'PUT','DELETE'])
def department_detail(request, name=None):
    """
    API endpoint for retrieving, updating, and deleting department details.

    Parameters:
    - request: The HTTP request object.
    - name (optional): The name of the department to retrieve, update, or delete.

    Returns:
    - GET: Returns a list of all departments.
    - POST: Creates a new department.
    - DELETE: Deletes the department with the specified name.

    Example Usage:
    - GET: /department/ - Retrieves a list of all departments.
    - PUT: /department-rename/{name} - Creates a new department.
    - DELETE:/department-delete/{name}/ - Deletes the department with the specified name.

    """
    if request.method == 'GET':
        departments = Site.objects.all()
        data = []
        for department in departments:
            guardoffice_name = department.guardoffice.name if department.guardoffice else None
            department_data = {
                'name': department.name,
                'guardoffice': guardoffice_name
            }
            data.append(department_data)
        return Response(data)

    elif request.method == 'POST':
        guardoffice_name = request.data.get('guardoffice')
        if not guardoffice_name:
            return Response({'error': 'Please specify the guardoffice'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            guardoffice = GuardOffice.objects.get(name=guardoffice_name)
        except GuardOffice.DoesNotExist:
            return Response({'error': 'Invalid guardoffice'}, status=status.HTTP_400_BAD_REQUEST)
        
        
        department_data = request.data
        department_data['guardoffice'] = guardoffice.pk  # assign the pk of the guardoffice
        serializer = SiteSerializer(data=department_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'PUT':
        new_department_name = request.data.get('name')
        if not new_department_name:
            return Response({'error': 'New department name not provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            department = Site.objects.get(name=name)
        except Site.DoesNotExist:
            return Response({'error': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)

        department.name = new_department_name
        department.save()

        return Response({'message': 'Department name updated successfully'}, status=status.HTTP_200_OK)
    
    elif request.method == 'DELETE':
        if name:
            try:
                department = Site.objects.get(name=name)
                department.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Site.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
    


# API endpoint for viewing all user's details.

class UserListView(APIView):
    def get(self, request, format=None):
        users = CustomUser.objects.all()
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data)



# API endpoint for managing Manager objects.
class ManagerView(APIView):
    def get(self, request):
        """
        Retrieves a list of all managers or a specific manager by email.

        GET Parameters:
        - email (optional): The email of the manager to retrieve.

        Example Usage:
        - GET: /manager/ - Retrieves a list of all managers.
        - GET: /manager/{email} - Retrieves a specific manager by email.
        """
        email = request.query_params.get('email')
        if email is not None:
            manager = GuardOfficeUser.objects.get(admin__email=email)
            serializer = GOUserSerializer(manager)
            return Response(serializer.data)
        else:
            managers = GuardOfficeUser.objects.all()
            serializer = GOUserSerializer(managers, many=True)
            return Response(serializer.data)

    def post(self, request):
        """
        Creates a new manager.

        POST Parameters:
        - All required fields for creating a manager.

        Example Usage:
        - POST: /manager/ - Creates a new manager.
        """
        serializer = GOUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, email):
        """
        Updates a manager by email.

        PUT Parameters:
        - email: The email of the manager to update.
        - All fields to be updated.

        Example Usage:
        - PUT: /manager/{email} - Updates a manager by email.
        """
        email = request.query_params.get('email')
        if email is None:
            return Response({'error': 'Email parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            manager = GuardOfficeUser.objects.get(admin__email=email)
        except GuardOfficeUser.DoesNotExist:
            return Response({'error': 'Manager not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = GOUserSerializer(manager, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, email):
        """
        Deletes a manager by email.

        DELETE Parameters:
        - email: The email of the manager to delete.

        Example Usage:
        - DELETE: /manager/{email} - Deletes a manager by email.
        """
        email = request.query_params.get('email')
        if email is None:
            return Response({'error': 'Email parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            manager = GuardOfficeUser.objects.get(admin__email=email)
        except GuardOfficeUser.DoesNotExist:
            return Response({'error': 'Manager not found'}, status=status.HTTP_404_NOT_FOUND)
        manager.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Guard 

class GuardHomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
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
            'sites': SiteSerializer(sites, many=True).data,
            'data_present': data_present,
            'data_absent': data_absent,
            'data_name': site_name,
            'sitename': site_name_value,
        }

        return Response(context)
    
    
class GuardViewAttendance(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        guard = get_object_or_404(Guard, admin=request.user)
        guard_office = get_object_or_404(GuardOffice, id=guard.guard_office.id)
        sites = Site.objects.filter(guard_office=guard_office)
        context = {
            'sites': SiteSerializer(sites, many=True).data,
        }
        return Response(context)

    def post(self, request, *args, **kwargs):
        guard = get_object_or_404(Guard, admin=request.user)
        site_name = request.data.get('site_name')
        start = request.data.get('start_date')
        end = request.data.get('end_date')
        try:
            site = get_object_or_404(Site, name=site_name)
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            attendance = Attendance.objects.filter(date__range=(start_date, end_date), site=site)
            attendance_reports = AttendanceReport.objects.filter(attendance__in=attendance, guard=guard)
            json_data = AttendanceReportSerializer(attendance_reports, many=True).data
            return Response(json_data)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        
class GuardViewSalary(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        guard = get_object_or_404(Guard, admin=request.user)
        salarys = GuardSalary.objects.filter(guard=guard)
        serializer = GuardSalarySerializer(salarys, many=True)
        return Response(serializer.data)
    
class GuardFeedback(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        guard = get_object_or_404(Guard, admin=request.user)
        feedbacks = FeedbackGuard.objects.filter(guard=guard)
        serializer = FeedbackGuardSerializer(feedbacks, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        guard = get_object_or_404(Guard, admin=request.user)
        data = request.data.copy()  # Make a mutable copy of request data
        data['guard'] = guard.id  # Assign the guard's ID
        serializer = FeedbackGuardSerializer(data=data)
        if serializer.is_valid():
            serializer.save(guard=guard)
            return Response({"success": "Feedback submitted successfully."}, status=201)
        return Response(serializer.errors, status=400)
    
class GuardApplyLeave(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        guard = get_object_or_404(Guard, admin=request.user)
        leave_history = LeaveReportGuard.objects.filter(guard=guard)
        context = {
            'leave_history': LeaveReportGuardSerializer(leave_history, many=True).data,
        }
        return Response(context)

    def post(self, request, *args, **kwargs):
        guard = get_object_or_404(Guard, admin=request.user)
        form = LeaveReportGuardForm(request.data)
        if form.is_valid():
            try:
                leave_date = form.cleaned_data.get('date')
                existing_leave = LeaveReportGuard.objects.filter(guard=guard, date=leave_date)
                if existing_leave.exists():
                    status_set = set(existing_leave.values_list('status', flat=True))
                    if 0 in status_set:  # Check if there are pending leaves
                        return Response({"error": "Leave Request for this Date is still Pending"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        status_text = [dict(LeaveReportGuard.STATUS_CHOICES).get(status, "Unknown") for status in status_set]
                        return Response({"error": f"Leave for this date has already been {', '.join(status_text)}"}, status=status.HTTP_400_BAD_REQUEST)
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

                    return Response({"success": "Application for leave has been submitted for review"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(error)
            return Response({"error": "Form has errors! " + ' '.join(error_messages)}, status=status.HTTP_400_BAD_REQUEST)

class CancelLeaveRequest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        guard = get_object_or_404(Guard, admin_id=request.user.id)
        leave_date = request.data.get('date')

        try:
            leave_date = datetime.strptime(leave_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        leave_report = get_object_or_404(LeaveReportGuard, guard=guard, date=leave_date)
        if leave_report.status == 0:  # Pending status
            leave_report.delete()
            return Response({"success": "Leave request cancelled successfully."}, status=200)
        else:
            return Response({"error": "Only pending leave requests can be cancelled."}, status=400)


class GuardViewProfile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        guard = get_object_or_404(Guard, admin=request.user)
        serializer = GuardSerializer(guard)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        guard = get_object_or_404(Guard, admin=request.user)
        admin_data = request.data.pop('admin', {})
        serializer = GuardSerializer(guard, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            # Update the admin (CustomUser) details
            admin = guard.admin
            admin.first_name = admin_data.get('first_name', admin.first_name)
            admin.last_name = admin_data.get('last_name', admin.last_name)
            admin.gender = admin_data.get('gender', admin.gender)
            admin.address = admin_data.get('address', admin.address)

            if 'profile_pic' in admin_data:
                admin.profile_pic = admin_data['profile_pic']
            
            admin.save()

            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    
class GuardViewNotification(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        guard = get_object_or_404(Guard, admin=request.user)
        notifications = NotificationGuard.objects.filter(guard=guard)
        serializer = NotificationGuardSerializer(notifications, many=True)
        return Response(serializer.data)
    
@api_view(['POST'])
def update_location(request):
    try:
        guard_email = request.data.get('guard_email')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        if not guard_email:
            return Response({"success": False, "error": "guard_email is required"}, status=status.HTTP_400_BAD_REQUEST)

        guard = get_object_or_404(Guard, admin__email=guard_email)
        
        GuardLocation.objects.update_or_create(
            guard=guard,
            defaults={'latitude': latitude, 'longitude': longitude, 'timestamp': timezone.now()}
        )

        return Response({"success": True, "message": "Location updated successfully."}, status=status.HTTP_200_OK)
    except KeyError as e:
        return Response({"success": False, "error": f"Missing key: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_guard_locations(request):
    locations = GuardLocation.objects.all()
    sites = Site.objects.all()
    
    guard_location_serializer = GuardLocationSerializer(locations, many=True)
    site_serializer = SiteSerializer(sites, many=True)
    
    return Response({
        "guard_locations": guard_location_serializer.data,
        "sites": site_serializer.data
    })