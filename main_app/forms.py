from django import forms
from django.forms.widgets import DateInput, TextInput
from django.core.exceptions import ValidationError
from .models import *
from datetime import datetime,date
from django.core.validators import RegexValidator

class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class CustomUserForm(FormSettings):
    email = forms.EmailField(required=True)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea)
    password = forms.CharField(widget=forms.PasswordInput)
    widget = {
        'password': forms.PasswordInput(),
    }
    profile_pic = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)

        if kwargs.get('instance'):
            instance = kwargs.get('instance').admin.__dict__
            self.fields['password'].required = False
            for field in CustomUserForm.Meta.fields:
                self.fields[field].initial = instance.get(field)
            if self.instance.pk is not None:
                self.fields['password'].widget.attrs['placeholder'] = "Fill this only if you wish to update password"

    def clean_email(self, *args, **kwargs):
        formEmail = self.cleaned_data['email'].lower()
        if self.instance.pk is None:  # Insert
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError(
                    "The given email is already registered")
        else:  # Update
            dbEmail = self.Meta.model.objects.get(
                id=self.instance.pk).admin.email.lower()
            if dbEmail != formEmail:  # There has been changes
                if CustomUser.objects.filter(email=formEmail).exists():
                    raise forms.ValidationError("The given email is already registered")

        return formEmail

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'gender',  'password','profile_pic', 'address' ]


class GuardForm(CustomUserForm):
    alphanumeric_validator = RegexValidator(
        r'^[a-zA-Z]*$',
        'Only alphabetic characters are allowed.'
    )

    first_name = forms.CharField(validators=[alphanumeric_validator])
    last_name = forms.CharField(validators=[alphanumeric_validator])
    
    def __init__(self, *args, **kwargs):
        super(GuardForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Guard
        fields = CustomUserForm.Meta.fields + \
            ['guard_office', 'site']

class ClientForm(CustomUserForm):
    site = forms.ModelChoiceField(queryset=Site.objects.all(), required=True)
    alphanumeric_validator = RegexValidator(
        r'^[a-zA-Z]*$',
        'Only alphabetic characters are allowed.'
    )
    first_name = forms.CharField(validators=[alphanumeric_validator])
    last_name = forms.CharField(validators=[alphanumeric_validator])
    
    def __init__(self, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        self.fields['site'].required = True  
    
    class Meta(CustomUserForm.Meta):
        model = Client
        fields = CustomUserForm.Meta.fields + ['company_name', 'vat_number', 'site']


class AdminClientForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(AdminClientForm, self).__init__(*args, **kwargs)
        self.fields['site'].required = True  
        
    class Meta(CustomUserForm.Meta):
        model = Client
        fields = CustomUserForm.Meta.fields + ['company_name', 'vat_number', 'site','guard_office']
        
class AdminForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Admin
        fields = CustomUserForm.Meta.fields


class GuardOfficeUserForm(CustomUserForm):
    alphanumeric_validator = RegexValidator(
        r'^[a-zA-Z]*$',
        'Only alphabetic characters are allowed.'
    )

    first_name = forms.CharField(validators=[alphanumeric_validator])
    last_name = forms.CharField(validators=[alphanumeric_validator])

    def __init__(self, *args, **kwargs):
        super(GuardOfficeUserForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = GuardOfficeUser
        fields = CustomUserForm.Meta.fields + \
            ['guard_office' ]


class GuardOfficeForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(GuardOfficeForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = ['name']
        model = GuardOffice


# class SiteForm(FormSettings):

#     def __init__(self, *args, **kwargs):
#         super(SiteForm, self).__init__(*args, **kwargs)

#     class Meta:
#         model = Site
#         fields = ['name', 'guard_office']

class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ['name', 'latitude', 'longitude', 'guard_office', 'radius'] 

    def __init__(self, *args, **kwargs):
        super(SiteForm, self).__init__(*args, **kwargs)
        self.fields['latitude'].widget = forms.HiddenInput()
        self.fields['longitude'].widget = forms.HiddenInput()
        self.fields['radius'].initial = 50 
        
class SiteLocationForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ['latitude', 'longitude']

    def __init__(self, *args, **kwargs):
        super(SiteLocationForm, self).__init__(*args, **kwargs)
        self.fields['latitude'].widget = forms.HiddenInput()
        self.fields['longitude'].widget = forms.HiddenInput()

class LeaveReportGOUserForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportGOUserForm, self).__init__(*args, **kwargs)
    
    def clean_date(self):
        leave_date_str = self.cleaned_data.get('date')
        if leave_date_str:
            # Convert the date string to a datetime.date object
            leave_date = datetime.strptime(leave_date_str, "%Y-%m-%d").date()
            if leave_date < date.today():
                raise ValidationError("The date cannot be in the past.")
            return leave_date
        return leave_date_str

    class Meta:
        model = LeaveReportGOUser
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class FeedbackGOUserForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(FeedbackGOUserForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackGOUser
        fields = ['feedback']

class FeedbackClientForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(FeedbackClientForm, self).__init__(*args, **kwargs)
        
    class Meta:
        model = FeedbackClient
        fields = ['feedback']
        
        
class LeaveReportGuardForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportGuardForm, self).__init__(*args, **kwargs)

    def clean_date(self):
        leave_date = self.cleaned_data.get('date')
        if leave_date < date.today():
            raise ValidationError("The date cannot be in the past.")
        return leave_date

    class Meta:
        model = LeaveReportGuard
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }
        
class FeedbackGuardForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(FeedbackGuardForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackGuard
        fields = ['feedback']


class GuardEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(GuardEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Guard
        fields = CustomUserForm.Meta.fields 


class GOUserEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(GOUserEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = GuardOfficeUser
        fields = CustomUserForm.Meta.fields


class EditSalaryForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(EditSalaryForm, self).__init__(*args, **kwargs)

    class Meta:
        model = GuardSalary
        fields = ['site', 'guard', 'base', 'ctc']


class ReviewForm(forms.Form):
    guard_id = forms.IntegerField(widget=forms.HiddenInput())
    rating = forms.ChoiceField(choices=[(i, i) for i in range(1, 6)])
    review = forms.CharField(widget=forms.Textarea, required=False)