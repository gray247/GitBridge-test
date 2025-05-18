import unittest
import requests

BASE_URL = "https://gitbridge.gray247.repl.co"

class TestGitBridgeAPI(unittest.TestCase):

    def test_root_endpoint(self):
        response = requests.get(BASE_URL + "/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("/upload", data["endpoints"])

    def test_tree_endpoint(self):
        response = requests.get(BASE_URL + "/tree")
        self.assertEqual(response.status_code, 200)

    def test_upload_missing_data(self):
        response = requests.post(BASE_URL + "/upload", json={})
        self.assertEqual(response.status_code, 400)

    def test_move_missing_data(self):
        response = requests.post(BASE_URL + "/move", json={})
        self.assertEqual(response.status_code, 400)

    @unittest.skip("Download endpoint not implemented yet")
    def test_download_missing_path(self):
        response = requests.get(BASE_URL + "/download")
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
