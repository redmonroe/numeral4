from selenium import webdriver
import unittest

class CreateUserTest(unittest.TestCase):


    def setUp(self):
        self.browser = webdriver.Firefox()


    def tearDown(self):
        self.browser.quit()  

    # def test_host_exists(self):
    #     self.browser.get('http://localhost:5000')

    #     self.assertIn('numeral4', self.browser.title)

    def test_login(self):
        self.browser.get('http://localhost:5000/login')

        self.assertIn('sign in', self.browser.title)

        self.fail('Finish the test!')

if __name__ == '__main__':
    unittest.main()



