import graphene
import os
from django.conf import settings
from django.core.files.storage import default_storage
from graphene_file_upload.scalars import Upload as UploadScalar
from graphql import GraphQLError
from blogs.models import Upload
from blogs.utils import save_uploaded_files
from .types import UploadType

class CreateUpload(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String(required=False)
        uploaded_images = graphene.List(UploadScalar, required=False)

    upload = graphene.Field(UploadType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, title, description="", uploaded_images=None):
        user_id = info.context.META.get('HTTP_X_USER_ID', '')
        print(f"🔍 MUTATION CALLED - user_id: {user_id}")
        print(f"🔍 uploaded_images: {uploaded_images}")
        print(f"🔍 uploaded_images type: {type(uploaded_images)}")
        
        if not user_id:
            raise GraphQLError("Authentication required. Please login.")
        
        image_paths = []
        if uploaded_images:
            print(f"🔍 Processing {len(uploaded_images)} images")
            image_paths = save_uploaded_files(uploaded_images, user_id)
        else:
            print("❌ No uploaded_images received")
        
        upload = Upload.objects.create(
            user_id=user_id,
            title=title,
            description=description,
            images=image_paths
        )
        
        return CreateUpload(
            upload=upload,
            success=True,
            message="Upload created successfully!"
        )


class UpdateUpload(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        title = graphene.String(required=False)
        description = graphene.String(required=False)
        uploaded_images = graphene.List(UploadScalar, required=False)

    upload = graphene.Field(UploadType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id, title=None, description=None, uploaded_images=None):
        user_id = info.context.META.get('HTTP_X_USER_ID', '')
        
        if not user_id:
            raise GraphQLError("Authentication required.")
        
        try:
            instance = Upload.objects.get(id=id)
        except Upload.DoesNotExist:
            raise GraphQLError("Upload not found.")
        
        if instance.user_id != user_id:
            raise GraphQLError("You don't have permission to edit this upload.")
        
        if title is not None:
            instance.title = title
        if description is not None:
            instance.description = description
        
        if uploaded_images:
            # Delete old images
            if instance.images:
                for old_image in instance.images:
                    old_path = os.path.join(settings.MEDIA_ROOT, old_image)
                    if os.path.exists(old_path):
                        os.remove(old_path)
            
            # Save new images
            image_paths = save_uploaded_files(uploaded_images, user_id)
            instance.images = image_paths
        
        instance.save()
        
        return UpdateUpload(
            upload=instance,
            success=True,
            message="Upload updated successfully!"
        )


class DeleteUpload(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id):
        user_id = info.context.META.get('HTTP_X_USER_ID', '')
        
        if not user_id:
            raise GraphQLError("Authentication required.")
        
        try:
            instance = Upload.objects.get(id=id)
        except Upload.DoesNotExist:
            raise GraphQLError("Upload not found.")
        
        if instance.user_id != user_id:
            raise GraphQLError("You don't have permission to delete this upload.")
        
        if instance.images:
            for image in instance.images:
                full_path = os.path.join(settings.MEDIA_ROOT, image)
                if os.path.exists(full_path):
                    os.remove(full_path)
        
        instance.delete()
        
        return DeleteUpload(
            success=True,
            message="Upload deleted successfully."
        )