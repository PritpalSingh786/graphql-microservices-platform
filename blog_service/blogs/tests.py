import json
from django.test import SimpleTestCase, Client
from blogs.models import Upload


class UploadGraphQLTests(SimpleTestCase):

    def setUp(self):
        self.client = Client()

        Upload.drop_collection()

        self.upload = Upload.objects.create(
            user_id="user123",
            title="Test Blog",
            description="Test Description",
            images=["uploads/test.jpg"]
        )

    def graphql_query(self, query, variables=None, user_id=None):
        headers = {}

        if user_id:
            headers["HTTP_X_USER_ID"] = user_id

        return self.client.post(
            "/graphql/",
            data=json.dumps({
                "query": query,
                "variables": variables or {}
            }),
            content_type="application/json",
            **headers
        )

    def test_get_all_uploads(self):
        query = """
        query {
            allUploads {
                id
                title
                description
                userId
                images
            }
        }
        """

        response = self.graphql_query(query)

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertNotIn("errors", data)
        self.assertEqual(len(data["data"]["allUploads"]), 1)
        self.assertEqual(
            data["data"]["allUploads"][0]["title"],
            "Test Blog"
        )

    def test_get_single_upload(self):
        query = """
        query($id: String!) {
            upload(id: $id) {
                id
                title
                description
            }
        }
        """

        response = self.graphql_query(
            query,
            {"id": str(self.upload.id)}
        )

        data = response.json()

        self.assertNotIn("errors", data)

        self.assertEqual(
            data["data"]["upload"]["title"],
            "Test Blog"
        )

    def test_my_uploads_authenticated(self):
        query = """
        query {
            myUploads {
                title
                userId
            }
        }
        """

        response = self.graphql_query(
            query,
            user_id="user123"
        )

        data = response.json()

        self.assertNotIn("errors", data)

        self.assertEqual(
            len(data["data"]["myUploads"]),
            1
        )

    def test_my_uploads_unauthenticated(self):
        query = """
        query {
            myUploads {
                title
            }
        }
        """

        response = self.graphql_query(query)

        data = response.json()

        self.assertNotIn("errors", data)

        self.assertEqual(
            len(data["data"]["myUploads"]),
            0
        )

    def test_create_upload(self):
        mutation = """
        mutation {
            createUpload(
                title: "New Upload",
                description: "New Description"
            ) {
                success
                message
                upload {
                    title
                    description
                    userId
                }
            }
        }
        """

        response = self.graphql_query(
            mutation,
            user_id="user123"
        )

        data = response.json()

        self.assertNotIn("errors", data)

        self.assertTrue(
            data["data"]["createUpload"]["success"]
        )

        self.assertEqual(
            data["data"]["createUpload"]["upload"]["title"],
            "New Upload"
        )

    def test_create_upload_without_auth(self):
        mutation = """
        mutation {
            createUpload(
                title: "New Upload"
            ) {
                success
                message
            }
        }
        """

        response = self.graphql_query(mutation)

        data = response.json()

        self.assertIn("errors", data)

    def test_update_upload(self):
        mutation = """
        mutation($id: ID!) {
            updateUpload(
                id: $id,
                title: "Updated Title",
                description: "Updated Description"
            ) {
                success
                message
                upload {
                    title
                    description
                }
            }
        }
        """

        response = self.graphql_query(
            mutation,
            {"id": str(self.upload.id)},
            user_id="user123"
        )

        data = response.json()

        self.assertNotIn("errors", data)

        self.assertTrue(
            data["data"]["updateUpload"]["success"]
        )

        self.assertEqual(
            data["data"]["updateUpload"]["upload"]["title"],
            "Updated Title"
        )

    def test_delete_upload(self):
        mutation = """
        mutation($id: ID!) {
            deleteUpload(id: $id) {
                success
                message
            }
        }
        """

        response = self.graphql_query(
            mutation,
            {"id": str(self.upload.id)},
            user_id="user123"
        )

        data = response.json()

        self.assertNotIn("errors", data)

        self.assertTrue(
            data["data"]["deleteUpload"]["success"]
        )

        self.assertEqual(
            Upload.objects.count(),
            0
        )

    def test_delete_upload_without_permission(self):
        mutation = """
        mutation($id: ID!) {
            deleteUpload(id: $id) {
                success
                message
            }
        }
        """

        response = self.graphql_query(
            mutation,
            {"id": str(self.upload.id)},
            user_id="another_user"
        )

        data = response.json()

        self.assertIn("errors", data)