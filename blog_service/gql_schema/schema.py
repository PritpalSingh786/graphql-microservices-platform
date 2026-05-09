import graphene
from .mutations import CreateUpload, UpdateUpload, DeleteUpload
from .queries import Query as BaseQuery

class Mutation(graphene.ObjectType):
    create_upload = CreateUpload.Field()
    update_upload = UpdateUpload.Field()
    delete_upload = DeleteUpload.Field()

class Query(BaseQuery):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)