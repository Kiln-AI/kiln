import unittest


class TestExample(unittest.TestCase):
    def test_a(self):
        self.assertEqual(42, 42)


if __name__ == "__main__":
    unittest.main()
