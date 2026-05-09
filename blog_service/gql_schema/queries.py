import graphene
from blogs.models import Upload
from .types import UploadType


class Query(graphene.ObjectType):
    all_uploads = graphene.List(UploadType)
    upload = graphene.Field(UploadType, id=graphene.String(required=True))
    my_uploads = graphene.List(UploadType)
    
    def resolve_all_uploads(self, info):
        return list(Upload.objects.all())
    
    def resolve_upload(self, info, id):
        try:
            return Upload.objects.get(id=id)
        except Upload.DoesNotExist:
            return None
    
    def resolve_my_uploads(self, info):
        user_id = info.context.META.get('HTTP_X_USER_ID', '')
        if not user_id:
            return []
        return list(Upload.objects.filter(user_id=user_id))