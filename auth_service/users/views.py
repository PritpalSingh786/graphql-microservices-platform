from django.shortcuts import render
from django.views import View
from django.contrib.auth import get_user_model
from .utils import verify_password_reset_token, secure_verify_password_reset_token, verify_email_token

User = get_user_model()


class VerifyEmailPageView(View):
    """Render email verification page"""
    
    def get(self, request):
        user_id = request.GET.get('user_id')
        token = request.GET.get('token')
        if not verify_email_token(user_id, token): 
            return render(request, 'users/email_verification_error.html', 
                          { 'message': 'Invalid or expired link. Please request a new one.' }) 
        return render(request, 'users/email_verification_success.html', 
                      { 'user_id': user_id, 'token': token })
        
       
class PasswordChangeTemplatePageView(View):
    """Render password reset template"""
    
    def get(self, request, user_id, token):
        if not verify_password_reset_token(user_id, token):
            return render(request, 'users/password_change_error.html', {
                'message': 'Invalid or expired link. Please request a new one.'
            })
        
        return render(request, 'users/password_change_template.html', {
            'user_id': user_id,
            'token': token
        })


class SecurePasswordChangeTemplatePageView(View):
    """Render secure password change template (for new login alert)"""
    
    def get(self, request, user_id, token):
        if not secure_verify_password_reset_token(user_id, token):
            return render(request, 'users/error.html', {
                'message': 'Invalid or expired link. Please request a new one.'
            })
        
        return render(request, 'users/secure_password_change_template.html', {
            'user_id': user_id,
            'token': token
        })