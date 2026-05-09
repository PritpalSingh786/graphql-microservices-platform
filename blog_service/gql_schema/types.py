import graphene
from blogs.models import Upload


class UploadType(graphene.ObjectType):
    id = graphene.String()
    user_id = graphene.String()
    title = graphene.String()
    description = graphene.String()
    images = graphene.List(graphene.String)
    created_at = graphene.DateTime()
    
    def resolve_id(self, info):
        return str(self.id)
    
    def resolve_user_id(self, info):
        return self.user_id
    
    def resolve_title(self, info):
        return self.title
    
    def resolve_description(self, info):
        return self.description
    
    def resolve_images(self, info):
        return self.images
    
    def resolve_created_at(self, info):
        return self.created_at