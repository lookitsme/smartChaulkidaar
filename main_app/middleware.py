from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.shortcuts import redirect

class LoginCheckMiddleWare(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__
        user = request.user

        if request.path.startswith('/api/'):
            return None  # Bypass API requests

        if user.is_authenticated:
            if user.user_type == '1':  # CEO/Admin
                if modulename == 'main_app.guard_views':
                    return redirect(reverse('admin_home'))
            elif user.user_type == '2':  # GuardOfficeUser
                if modulename in ['main_app.guard_views', 'main_app.ceo_views']:
                    return redirect(reverse('guardofficeuser_home'))
            elif user.user_type == '3':  # Guard
                if modulename in ['main_app.ceo_views', 'main_app.guardofficeuser_views']:
                    return redirect(reverse('guard_home'))
            elif user.user_type == '4':  # Client
                if modulename in ['main_app.ceo_views', 'main_app.guardofficeuser_views', 'main_app.guard_views']:
                    return redirect(reverse('client_home'))
            else:
                return redirect(reverse('login_page'))
        else:
            if request.path == reverse('login_page') or modulename == 'django.contrib.auth.views' or request.path == reverse('user_login'):
                pass
            else:
                return redirect(reverse('login_page'))