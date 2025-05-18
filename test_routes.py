import unittest
import requests

BASE_URL = "http://localhost:8080"

class TestGitBridgeRoutes(unittest.TestCase):

    def setUp(self):
        # Upload fresh file before each test
        requests.post(BASE_URL + "/upload", json={
            "path": "demo/test_route.txt",
            "content": "Test file for move and delete"
        })

    def test_upload_route(self):
        data = {
            "path": "demo/test_upload.txt",
            "content": "This is a test file"
        }
        response = requests.post(BASE_URL + "/upload", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Uploaded", response.text)

    def test_tree_route(self):
        response = requests.get(BASE_URL + "/tree")
        self.assertEqual(response.status_code, 200)
        self.assertIn("files", response.json())

    def test_move_route(self):
        data = {
            "src": "demo/test_route.txt",
            "dst": "archive/test_route.txt"
        }
        response = requests.post(BASE_URL + "/move", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Moved", response.text)

    def test_delete_route(self):
        # Ensure file is moved before deleting
        requests.post(BASE_URL + "/move", json={
            "src": "demo/test_route.txt",
            "dst": "archive/test_route.txt"
        })
        response = requests.post(BASE_URL + "/delete", json={
            "path": "archive/test_route.txt"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Deleted", response.text)

    def test_missing_upload_data(self):
        response = requests.post(BASE_URL + "/upload", json={})
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()