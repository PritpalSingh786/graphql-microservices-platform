from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from gql_schema.schema import schema  # Change: import 'schema' not 'Schema'
from django.contrib import admin
from users import views

class CustomGraphQLView(GraphQLView):
    schema = schema  # Change: use 'schema' variable
    
    def parse_body(self, request):
        return super().parse_body(request)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(CustomGraphQLView.as_view(graphiql=True))),

    # Template URLs for email links (REST endpoints for templates)
    path('verify-email/', views.VerifyEmailPageView.as_view(), name='verify-email'),
    path('password-change-template/<uuid:user_id>/<str:token>/', 
         views.PasswordChangeTemplatePageView.as_view(), 
         name='password-change-template'),
    path('secure-password-change-template/<uuid:user_id>/<str:token>/', 
         views.SecurePasswordChangeTemplatePageView.as_view(), 
         name='secure-password-change-template'),
]