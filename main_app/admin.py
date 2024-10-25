from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from django.contrib.admin.sites import NotRegistered

class CustomUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

# Unregister the model before registering it again
try:
    admin.site.unregister(CustomUser)
except NotRegistered:
    pass

admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(GuardOfficeUser)
admin.site.register(Guard)
admin.site.register(GuardOffice)
admin.site.register(Site)
admin.site.register(Client)
admin.site.register(Attendance)