from rest_framework import serializers
from main_app.models import *

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'user_type', 'gender', 'profile_pic', 'address']
        extra_kwargs = {
            'email': {'read_only': True}
        }
        
class GuardOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuardOffice
        fields = ['id', 'name']

# class CustomUserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ['email', 'user_type', 'gender', 'profile_pic', 'address', 'created_at', 'updated_at']

class GOUserSerializer(serializers.ModelSerializer):
    guardoffice = GuardOfficeSerializer(read_only=True)
    admin = CustomUserSerializer(read_only=True)
    type_2_user = CustomUserSerializer(many=True, read_only=True)

    class Meta:
        model = GuardOfficeUser
        fields = ['guardoffice', 'admin', 'type_2_user']
        
class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = '__all__'

# Guard 

class GuardSerializer(serializers.ModelSerializer):
    admin = CustomUserSerializer(read_only=True)
    guard_office = GuardOfficeSerializer(read_only=True)
    site = SiteSerializer(read_only=True)
    class Meta:
        model = Guard
        fields = '__all__'
        extra_kwargs = {
            'admin': {'required': False}
        }
        
class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = '__all__'

class AttendanceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceReport
        fields = '__all__'

class LeaveReportGuardSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveReportGuard
        fields = '__all__'

class FeedbackGuardSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackGuard
        fields = '__all__'
        extra_kwargs = {
            'reply': {'required': False},
            'guard': {'required': False}
        }

class NotificationGuardSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationGuard
        fields = '__all__'

class GuardSalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = GuardSalary
        fields = '__all__'

class GuardLocationSerializer(serializers.ModelSerializer):
    guard_name = serializers.SerializerMethodField()
    guard_email = serializers.EmailField(source='guard.admin.email', read_only=True)
    guard_site = serializers.CharField(source='guard.site.name', read_only=True)

    class Meta:
        model = GuardLocation
        fields = ['guard_name', 'guard_email', 'guard_site', 'latitude', 'longitude', 'timestamp']
        
    def get_guard_name(self, obj):
        first_name = obj.guard.admin.first_name.title()
        last_name = obj.guard.admin.last_name.title()
        return f"{first_name} {last_name}"

class SiteSerializer(serializers.ModelSerializer):
    guards = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = ['name', 'latitude', 'longitude', 'guards']

    def get_guards(self, obj):
        return [guard.admin.get_full_name() for guard in obj.guard_set.all()]