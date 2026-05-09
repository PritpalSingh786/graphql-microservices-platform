from django.contrib import admin
from .models import Upload

# try:
#     admin.site.register(Upload)
# except TypeError:
#     pass  # MongoDB document ke liye admin registration skip karo