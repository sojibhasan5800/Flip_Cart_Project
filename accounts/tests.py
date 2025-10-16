# accounts/tests/test_accounts.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Account, UserProfile
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken

def get_jwt_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class AccountsAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('accounts_api:register')
        self.login_url = reverse('accounts_api:login')
        self.dashboard_url = reverse('accounts_api:dashboard')
        # create a user
        self.user = Account.objects.create_user(
            first_name='Test', last_name='User', email='testuser@example.com',
            username='testuser', password='strongpassword123'
        )
        # ensure user active for tests
        self.user.is_active = True
        self.user.save()
        UserProfile.objects.get_or_create(user=self.user)

    def test_register_success(self):
        data = {
            "first_name":"Alice",
            "last_name":"Bob",
            "phone_number":"0123456789",
            "email":"alice@example.com",
            "password":"newpass123",
            "confirm_password":"newpass123"
        }
        resp = self.client.post(self.register_url, data, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Account.objects.filter(email="alice@example.com").exists())

    def test_register_password_mismatch(self):
        data = {
            "first_name":"X",
            "last_name":"Y",
            "phone_number":"0",
            "email":"mismatch@example.com",
            "password":"a",
            "confirm_password":"b"
        }
        resp = self.client.post(self.register_url, data, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_login_success_returns_token(self):
        data = {"email": "testuser@example.com", "password": "strongpassword123"}
        resp = self.client.post(self.login_url, data, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("token", resp.data)

    def test_login_invalid_credentials(self):
        data = {"email": "testuser@example.com", "password": "wrong"}
        resp = self.client.post(self.login_url, data, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_dashboard_requires_auth(self):
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 401)  # unauthorized

    def test_dashboard_with_token(self):
        token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('orders_count', resp.data)

    def test_change_password_wrong_current(self):
        access_token = get_jwt_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        url = reverse('accounts_api:change_password')
        resp = self.client.post(url, {
            'current_password': 'bad',
            'new_password': 'newstrong123',
            'confirm_password': 'newstrong123'
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_change_password_success(self):
        access_token = get_jwt_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        url = reverse('accounts_api:change_password')
        resp = self.client.post(url, {
            'current_password': 'strongpassword123',
            'new_password': 'newstrong123',
            'confirm_password': 'newstrong123'
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        # verify login with new password
        self.client.credentials()  # remove auth
        resp2 = self.client.post(self.login_url, {'email': 'testuser@example.com', 'password': 'newstrong123'}, format='json')
        self.assertEqual(resp2.status_code, 200)
