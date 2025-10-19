# carts/tests/test_cart_api.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from store.models import Product
from carts.models import CartItem, Cart
from accounts.models import Account

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    """Return DRF API client instance"""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a dummy user"""
    return Account.objects.create_user(
        first_name="Sojib",
        last_name="Hasan",
        username="sojib5800",
        email="sojib@example.com",
        password="1234abcd"
    )


@pytest.fixture
def product(db):
    """Create a sample product"""
    return Product.objects.create(
        product_name="Test Product",
        price=100,
        stock=10,
        slug="test-product"
    )


@pytest.fixture
def cart(user):
    """Create a cart for authenticated or anonymous users"""
    return Cart.objects.create(cart_id="session_1234")


# -----------------------------
# Cart Item API Tests
# -----------------------------
class TestCartItemAPI:
    endpoint = reverse("carts_api:cart_items")

    def test_get_cart_items_anonymous_user(self, api_client, product):
        """Anonymous users now cannot access cart items (403)"""
        cart = Cart.objects.create(cart_id="anon_123")
        CartItem.objects.create(product=product, cart=cart, quantity=2)
        response = api_client.get(self.endpoint)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_cart_items_anonymous_user_forbidden(self, api_client, product):
        """Anonymous users now cannot add product to cart (403)"""
        payload = {"product_id": product.id, "quantity": 3}
        response = api_client.post(self.endpoint, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_add_product_to_cart_anonymous_forbidden(self, api_client, product):
        """Authenticated user can add a product to their cart"""
        api_client.force_authenticate(user=user)
        payload = {"product_id": product.id, "quantity": 1}
        response = api_client.post(self.endpoint, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["quantity"] == 1
        assert response.data["product"]["product_name"] == product.product_name

    def test_add_existing_product_increases_quantity(self, api_client, user, product):
        """Adding the same product again increases quantity"""
        api_client.force_authenticate(user=user)
        CartItem.objects.create(user=user, product=product, quantity=2)
        payload = {"product_id": product.id, "quantity": 3}
        response = api_client.post(self.endpoint, payload)
        assert response.status_code == status.HTTP_201_CREATED
        item = CartItem.objects.get(user=user, product=product)
        assert item.quantity == 5  # 2 + 3 = 5

    def test_update_cart_item_quantity(self, api_client, user, product):
        """User can update the quantity of an existing cart item"""
        api_client.force_authenticate(user=user)
        item = CartItem.objects.create(user=user, product=product, quantity=2)
        url = reverse("carts_api:cart_item_detail", args=[item.id])
        payload = {"quantity": 5}
        response = api_client.put(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        item.refresh_from_db()
        assert item.quantity == 5

    def test_delete_cart_item(self, api_client, user, product):
        """User can delete a cart item"""
        api_client.force_authenticate(user=user)
        item = CartItem.objects.create(user=user, product=product, quantity=2)
        url = reverse("carts_api:cart_item_detail", args=[item.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CartItem.objects.filter(id=item.id).exists()

    def test_put_with_zero_quantity_removes_item(self, api_client, user, product):
        """If quantity <= 0, the item should be deleted automatically"""
        api_client.force_authenticate(user=user)
        item = CartItem.objects.create(user=user, product=product, quantity=3)
        url = reverse("carts_api:cart_item_detail", args=[item.id])
        response = api_client.put(url, {"quantity": 0}, format="json")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CartItem.objects.filter(id=item.id).exists()

    def test_cart_item_sub_total_calculation(self, user, product):
        """Ensure sub_total() returns correct value"""
        item = CartItem.objects.create(user=user, product=product, quantity=4)
        assert item.sub_total() == product.price * 4
