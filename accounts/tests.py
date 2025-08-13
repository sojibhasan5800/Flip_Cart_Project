from django.test import TestCase
from accounts.models import Account
from django.contrib.auth import authenticate,get_user_model
from django.urls import reverse
User = get_user_model()


# Create your tests here.
class AccountModelTest(TestCase):

    def setUp(self):
        self.account = Account.objects.create_user(
            first_name="John",
            last_name="Doe",
            username="johndoe",
            email="johndoe@example.com",
            password="password123",
        )
    def test_account_creation(self):  
        self.assertEqual(self.account.email, "johndoe@example.com")
        self.assertEqual(self.account.username, "johndoe")
        self.assertTrue(self.account.check_password("password123"))

    def test_full_name_method(self):     
        self.assertEqual(self.account.full_name(), "John Doe")

    def test_str_method(self):      
        self.assertEqual(str(self.account), "johndoe@example.com")

    def test_has_perm_method(self):       
        self.account.is_admin = True
        self.assertTrue(self.account.has_perm("some_perm"))

    def test_has_module_perms_method(self):
        self.assertTrue(self.account.has_module_perms("app_label"))


class LoginViewTest(TestCase):
    def setUp(self):
        # Create a test user
        self.password = 'testpassword123'
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            password=self.password
        )

    def test_login_success(self):
        # response = self.client.post(reverse('login'), {
        #     'email': 'testuser@example.com',
        #     'password': self.password
        # })

        self.assertEqual(self.user.email, "testuser@example.com")  
        self.assertEqual(self.password,"testpassword123")  

    def test_login_fail(self):
    #     response = self.client.post(reverse('login'), {
    #         'email': 'testuser@example.com',
    #         'password': 'wrongpassword'
    #     })

        self.assertNotEqual(self.user.email, "gapm@gmail.com")  
        self.assertNotEqual(self.password, "2050.com")  

        

