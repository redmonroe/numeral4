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

'''

from selenium import webdriver
import unittest
from selenium.webdriver.common.keys import Keys



class FirstLogin(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()


    # end to her: price, security, portability, does not need web
    #connection, (credentials hosted locally?), never adds or sales in the app
    def tearDown(self):
        self.browser.quit()

    def test_can_hit_landing_page(self):

         # Edith has heard about a cool new online finance app. She goes to check out its homepage
        self.browser.get('http://localhost:5000')

        # Like many she has anxiety about finances, they are difficult, boring, some detailed missed ends up being the most important part: what does Edith get from numeral4?
        self.assertIn('numeral4', self.browser.title)
        
        header = self.browser.find_element_by_tag_name('h1')
        assert 'numeral4' in header.text

        body = self.browser.find_element_by_tag_name('body')
        assert 'what does Edith get from numeral4?' in body.text

        login_link = self.browser.find_element_by_link_text('signup')
        assert 'signup' in login_link.text

# def test_can_hit_signup_page(self):

        self.browser.get('http://localhost:5000/signup/')

        inputbox = self.browser.find_element_by_name('username_box')
        inputbox.send_keys('test_boy')
        inputbox.send_keys(Keys.ENTER)
'''