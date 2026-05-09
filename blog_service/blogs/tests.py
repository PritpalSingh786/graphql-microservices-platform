from django.test import TestCase
from blogs.models import Upload
import uuid


class UploadModelTest(TestCase):
    def test_create_upload(self):
        upload = Upload.objects.create(
            user_id='test-user-123',
            title='Test Blog',
            description='This is a test blog post',
            images=['image1.jpg', 'image2.jpg']
        )
        self.assertEqual(upload.title, 'Test Blog')
        self.assertEqual(upload.user_id, 'test-user-123')
        self.assertEqual(len(upload.images), 2)

    def test_upload_str_method(self):
        upload = Upload.objects.create(
            user_id='test-user-456',
            title='My Blog Post',
            description='Test description'
        )
        self.assertEqual(str(upload), 'My Blog Post')

    def test_upload_id_is_uuid(self):
        upload = Upload.objects.create(
            user_id='user1',
            title='UUID Test',
            description='Testing UUID'
        )
        self.assertTrue(upload.id)
        self.assertEqual(len(upload.id), 36)

    def test_upload_ordering(self):
        upload1 = Upload.objects.create(
            user_id='user1',
            title='First Post',
            description='Desc1'
        )
        upload2 = Upload.objects.create(
            user_id='user1',
            title='Second Post',
            description='Desc2'
        )
        uploads = Upload.objects.all()
        self.assertEqual(uploads[0].title, 'Second Post')


class GraphQLBlogTest(TestCase):
    def setUp(self):
        self.upload = Upload.objects.create(
            user_id='test-user-graphql',
            title='GraphQL Test Post',
            description='Testing GraphQL queries'
        )

    def test_all_uploads_query(self):
        from graphene.test import Client
        from gql_schema.schema import schema
        
        client = Client(schema)
        executed = client.execute('''
            query {
                allUploads {
                    id
                    title
                    description
                }
            }
        ''')
        self.assertIsNotNone(executed['data']['allUploads'])
        self.assertEqual(len(executed['data']['allUploads']), 1)
        self.assertEqual(executed['data']['allUploads'][0]['title'], 'GraphQL Test Post')