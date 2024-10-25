from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import AbstractUser

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from datetime import timedelta



class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = CustomUser(email=email, **extra_fields)
        user.password = make_password(password) # Hashing password
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):# Create user Public method
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        assert extra_fields["is_staff"]
        assert extra_fields["is_superuser"]
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    USER_TYPE = ((1, "CEO"), (2, "GuardOfficeUser"), (3, "Guard"), (4, "Client"))
    GENDER = [("M", "Male"), ("F", "Female")]
    
    
    username = None  # Removed username, using email instead
    email = models.EmailField(unique=True)
    user_type = models.CharField(default=1, choices=USER_TYPE, max_length=1)
    gender = models.CharField(max_length=1, choices=GENDER)
    profile_pic = models.ImageField(null=True, blank=True, default="admin/image/default.jpg")
    address = models.TextField()
    fcm_token = models.TextField(default="")  # For firebase notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()


    def __str__(self):
        return self.last_name + ", " + self.first_name


class Admin(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    


class GuardOffice(models.Model): # Division - > Guard Office 
    name = models.CharField(max_length=120)
    total_leave_days = models.IntegerField(default=25)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class GuardOfficeUser(models.Model): # Manager -> Guard Office Manager,
    guard_office = models.ForeignKey(GuardOffice, on_delete=models.DO_NOTHING, null=True, blank=False)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
        
    def __str__(self):
        return self.admin.last_name + " " + self.admin.first_name


class Site(models.Model):
    name = models.CharField(max_length=120)
    guard_office = models.ForeignKey(GuardOffice, on_delete=models.CASCADE)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    radius = models.IntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    # + " - " + "Created at " + self.created_at.strftime("%Y-%m-%d")


class Guard(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    guard_office = models.ForeignKey(GuardOffice, on_delete=models.DO_NOTHING, null=True, blank=True)
    individual_leave_days = models.IntegerField(null=True, blank=True) 
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True)
    average_rating = models.FloatField(default=0.0) 
    review_count = models.IntegerField(default=0)  
    is_checked_in = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.admin.email} - {self.admin.last_name}, {self.admin.first_name}"

class Client(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255, default="")
    vat_number = models.CharField(max_length=255, default="")
    guard_office = models.ForeignKey(GuardOffice, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.admin.email} - {self.company_name}, {self.vat_number}"
      
class GuardLocation(models.Model):
    guard = models.ForeignKey(Guard, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Location of {self.guard.admin.email} at {self.timestamp}"
    
class Attendance(models.Model):
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class AttendanceReport(models.Model):
    guard = models.ForeignKey(Guard, on_delete=models.DO_NOTHING)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    duration = models.DurationField(default=timedelta(0))

class AttendanceLog(models.Model):
    guard = models.ForeignKey(Guard, on_delete=models.CASCADE)
    check_in_time = models.DateTimeField()
    check_out_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.guard.admin.email} - {self.check_in_time} to {self.check_out_time}"
    
class Complaint(models.Model):
    guard = models.ForeignKey(Guard, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint against {self.guard.admin.email} by {self.client.admin.email}"
    
class LeaveReportGuard(models.Model):
    STATUS_CHOICES = [
        (0, 'Pending'),
        (1, 'Approved'),
        (-1, 'Rejected'),
    ]
    # leave_count = models.IntegerField(default=25)
    guard = models.ForeignKey(Guard, on_delete=models.CASCADE)
    date = models.DateField() 
    message = models.TextField()
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportGOUser(models.Model):
    guardofficeuser = models.ForeignKey(GuardOfficeUser, on_delete=models.CASCADE)
    date = models.DateField()
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackGuard(models.Model):
    guard = models.ForeignKey(Guard, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackGOUser(models.Model):
    guardofficeuser = models.ForeignKey(GuardOfficeUser, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class FeedbackClient(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Notification(models.Model):
    admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)
    is_complaint = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.email}"

class NotificationGOUser(models.Model):
    guardofficeuser = models.ForeignKey(GuardOfficeUser, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_complaint = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False) 
    
    def __str__(self):
        return f"Notification for {self.guardofficeuser.admin.email}"


class NotificationGuard(models.Model):
    guard = models.ForeignKey(Guard, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False) 


class GuardSalary(models.Model):
    guard = models.ForeignKey(Guard, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    base = models.FloatField(default=0)
    ctc = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class GuardReview(models.Model):
    guard = models.ForeignKey(Guard, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    rating = models.IntegerField()
    review = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('guard', 'client') 
    def __str__(self):
        return f"Review for {self.guard.admin.email} by {self.client.admin.email}"

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:
            Admin.objects.create(admin=instance)
        if instance.user_type == 2:
            GuardOfficeUser.objects.create(admin=instance)
        if instance.user_type == 3:
            Guard.objects.create(admin=instance)
        if instance.user_type == 4:
            pass


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 1:
        instance.admin.save()
    if instance.user_type == 2:
        instance.guardofficeuser.save()
    if instance.user_type == 3:
        instance.guard.save()
    elif instance.user_type == 4 and hasattr(instance, 'client'):
        instance.client.save()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance) 