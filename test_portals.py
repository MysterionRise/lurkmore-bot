import unittest

from lurkmore_bot import Wikipedia


class TestWikipedia(unittest.TestCase):
    def test_get_image_url(self):
        wikipedia = Wikipedia("https://en.wikipedia.org/wiki/Special:Random")
        test_cases = [
            "https://en.wikipedia.org/wiki/OpenAI",
            "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "https://en.wikipedia.org/wiki/Don_Mattera",
            "https://en.wikipedia.org/wiki/Saint-Plaisir",
        ]
        for url in test_cases:
            with self.subTest(url=url):
                result_url = wikipedia.get_image_url(url)
                self.assertIsNotNone(result_url)


if __name__ == "__main__":
    unittest.main()
