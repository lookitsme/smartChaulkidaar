from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib import messages
from .models import Site, GuardOfficeUser, Guard, GuardSalary
from .forms import EditSalaryForm
from django.urls import reverse


class EditSalaryView(View):
    def get(self, request, *args, **kwargs):
        salaryForm = EditSalaryForm()
        guardofficeuser = get_object_or_404(GuardOfficeUser, admin=request.user)
        salaryForm.fields['site'].queryset = Site.objects.filter(guard_office=guardofficeuser.guard_office)
        context = {
            'form': salaryForm,
            'page_title': "Edit Employee's Salary"
        }
        return render(request, "guardofficeuser_template/edit_guard_salary.html", context)

    def post(self, request, *args, **kwargs):
        form = EditSalaryForm(request.POST)
        context = {'form': form, 'page_title': "Edit Employee's Salary"}
        if form.is_valid():
            try:
                guard = form.cleaned_data.get('guard')
                site = form.cleaned_data.get('site')
                base = form.cleaned_data.get('base')
                ctc = form.cleaned_data.get('ctc')
                # Validating
                salary = GuardSalary.objects.get(guard=guard, site=site)
                salary.ctc = ctc
                salary.base = base
                salary.save()
                messages.success(request, "Salary Updated")
                return redirect(reverse('edit_guard_salary'))
            except Exception as e:
                messages.warning(request, "Salary Could Not Be Updated")
        else:
            messages.warning(request, "Salary Could Not Be Updated")
        return render(request, "guardofficeuser_template/edit_guard_salary.html", context)
