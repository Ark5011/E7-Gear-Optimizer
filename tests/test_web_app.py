import unittest

from web_app import app


class WebAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True)
        cls.client = app.test_client()

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Gear evaluator", response.data)

    def test_text_analysis_renders_recommendation(self):
        response = self.client.post(
            "/",
            data={
                "action": "analyze",
                "ocr_text": "Speed 5\nCritical Hit Chance 8%\nAttack 8%",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Roll", response.data)


if __name__ == "__main__":
    unittest.main()
