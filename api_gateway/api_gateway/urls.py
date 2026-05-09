from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/auth/', include('apps.auth_gateway.urls')),
    path('graphql/blog/', include('apps.blog_gateway.urls')),
]