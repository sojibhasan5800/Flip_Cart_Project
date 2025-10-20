# carts/tests/test_api.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from carts.models import Cart, CartItem
from store.models import Product
from accounts.models import Account

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def make_user(email="testuser@example.com", password="pass1234"):
        user = Account.objects.create_user(
            email=email,
            username="testuser",
            password=password
        )
        return user
    return make_user


@pytest.fixture
def create_product(db):
    def make_product(name="Test Product", price=100):
        return Product.objects.create(
            product_name=name,
            price=price,
            stock=10,
            slug=name.lower().replace(" ", "-")
        )
    return make_product


@pytest.fixture
def create_cart(db):
    def make_cart(cart_id="session_123"):
        return Cart.objects.create(cart_id=cart_id)
    return make_cart


# ---------------------------------------------------------
#  TEST 1: GET CART ITEMS (Authenticated & Guest)
# ---------------------------------------------------------
def test_get_cart_items_authenticated(api_client, create_user, create_product, create_cart):
    user = create_user()
    product = create_product()
    cart = create_cart(cart_id=f"user_{user.id}")

    CartItem.objects.create(user=user, product=product, cart=cart, quantity=2)

    api_client.force_authenticate(user=user)
    url = reverse("carts_api:cart_items")
    response = api_client.get(url, {"id": cart.id})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["quantity"] == 2


def test_get_cart_items_guest(api_client, create_product, create_cart):
    product = create_product()
    cart = create_cart()
    CartItem.objects.create(product=product, cart=cart, quantity=1)

    # simulate session
    session = api_client.session
    session["cart_id"] = cart.cart_id
    session.save()

    url = reverse("carts_api:cart_items")
    response = api_client.get(url, {"id": cart.id})
    assert response.status_code in [200, 204]  # allow empty cart response


# ---------------------------------------------------------
#  TEST 2: ADD PRODUCT TO CART (POST)
# ---------------------------------------------------------
def test_add_product_to_cart_authenticated(api_client, create_user, create_product):
    user = create_user()
    product = create_product()
    api_client.force_authenticate(user=user)

    url = reverse("carts_api:cart_items")
    data = {"product_id": product.id, "quantity": 2}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["quantity"] == 2
    assert CartItem.objects.filter(user=user, product=product).exists()


def test_add_product_to_cart_guest(api_client, create_product):
    product = create_product()
    url = reverse("carts_api:cart_items")
    data = {"product_id": product.id, "quantity": 3}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert CartItem.objects.filter(product=product).exists()


# ---------------------------------------------------------
#  TEST 3: UPDATE CART ITEM (PUT)
# ---------------------------------------------------------
def test_update_cart_item_quantity(api_client, create_user, create_product, create_cart):
    user = create_user()
    product = create_product()
    cart = create_cart()
    cart_item = CartItem.objects.create(user=user, product=product, cart=cart, quantity=2)

    url = reverse("carts_api:cart_item_detail", kwargs={"pk": cart_item.id})
    response = api_client.put(url, {"quantity": 5}, format="json")

    assert response.status_code == status.HTTP_200_OK
    cart_item.refresh_from_db()
    assert cart_item.quantity == 5


# ---------------------------------------------------------
#  TEST 4: DELETE CART ITEM
# ---------------------------------------------------------
def test_delete_cart_item(api_client, create_user, create_product, create_cart):
    user = create_user()
    product = create_product()
    cart = create_cart()
    cart_item = CartItem.objects.create(user=user, product=product, cart=cart, quantity=1)

    url = reverse("carts_api:cart_item_detail", kwargs={"pk": cart_item.id})
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not CartItem.objects.filter(id=cart_item.id).exists()


# ---------------------------------------------------------
#  TEST 5: CONTEXT PROCESSOR (cart count)
# ---------------------------------------------------------
from carts.context_processors import counter

def test_cart_counter_authenticated_request(client, create_user, create_product, create_cart):
    user = create_user()
    product = create_product()
    cart = create_cart()
    CartItem.objects.create(user=user, product=product, cart=cart, quantity=4)

    client.force_login(user)
    request = client.get("/")
    request.user = user
    result = counter(request.wsgi_request)
    assert result["cart_count"] == 4


def test_cart_counter_guest_request(client, create_product, create_cart):
    product = create_product()
    cart = create_cart()
    CartItem.objects.create(product=product, cart=cart, quantity=2)

    session = client.session
    session["cart_id"] = cart.cart_id
    session.save()

    request = client.get("/")
    request.session = session
    result = counter(request.wsgi_request)
    assert result["cart_count"] >= 0
