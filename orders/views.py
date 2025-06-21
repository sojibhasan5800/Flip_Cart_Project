from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from carts.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from sslcommerz_lib import SSLCOMMERZ 
import random
import string
import time
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from django.urls import reverse



def generate_transaction_id():
    timestamp = int(time.time())  # current Unix time (e.g., 1724312820)
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))  # e.g., 'A1B2C3'
    return f"TXN{timestamp}{random_str}"



# def payments(request):
#     body = json.loads(request.body)
#     order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

#     # Store transaction details inside Payment model
#     payment = Payment(
#         user = request.user,
#         payment_id = body['transID'],
#         payment_method = body['payment_method'],
#         amount_paid = order.order_total,
#         status = body['status'],
#     )
#     payment.save()

#     order.payment = payment
#     order.is_ordered = True
#     order.save()

#     # Move the cart items to Order Product table
#     cart_items = CartItem.objects.filter(user=request.user)

#     for item in cart_items:
#         orderproduct = OrderProduct()
#         orderproduct.order_id = order.id
#         orderproduct.payment = payment
#         orderproduct.user_id = request.user.id
#         orderproduct.product_id = item.product_id
#         orderproduct.quantity = item.quantity
#         orderproduct.product_price = item.product.price
#         orderproduct.ordered = True
#         orderproduct.save()

#         cart_item = CartItem.objects.get(id=item.id)
#         product_variation = cart_item.variations.all()
#         orderproduct = OrderProduct.objects.get(id=orderproduct.id)
#         orderproduct.variations.set(product_variation)
#         orderproduct.save()


#         # Reduce the quantity of the sold products
#         product = Product.objects.get(id=item.product_id)
#         product.stock -= item.quantity
#         product.save()

#     # Clear cart
#     CartItem.objects.filter(user=request.user).delete()

#     # Send order recieved email to customer
#     mail_subject = 'Thank you for your order!'
#     message = render_to_string('orders/order_recieved_email.html', {
#         'user': request.user,
#         'order': order,
#     })
#     to_email = request.user.email
#     send_email = EmailMessage(mail_subject, message, to=[to_email])
#     send_email.send()

#     # Send order number and transaction id back to sendData method via JsonResponse
#     data = {
#         'order_number': order.order_number,
#         'transID': payment.payment_id,
#     }
#     return JsonResponse(data)


def payments(request,id,tk=0):
    current_user = request.user
    print( request.user.email)
    customer_details = Order.objects.get(user = current_user,id=id)
    token, _ = Token.objects.get_or_create(user=current_user)
    email = request.user.email
    transction_id = generate_transaction_id()
    print(current_user)



    base_url = f"{request.scheme}://{request.get_host()}"
    print(base_url)
    success_path = reverse('payment_success')  # will be /accounts/payment/success/
    success_url = f"{base_url}{success_path}?email={email}&status=success&transction_id={transction_id}&payment_method=Bkash&paid={tk}&user={current_user}"
    fail_url    = f"{base_url}{success_path}?email={email}&status=fail"
    cancel_url  = f"{base_url}{success_path}?email={email}&status=cancel"

    settings = { 'store_id': 'trans68369e6df24cb', 'store_pass': 'trans68369e6df24cb@ssl', 'issandbox': True }
    sslcz = SSLCOMMERZ(settings)
    post_body = {}
    post_body['total_amount'] = tk
    post_body['currency'] = "BDT"
    post_body['tran_id'] = transction_id
    post_body['success_url'] = success_url
    post_body['fail_url'] = fail_url
    post_body['cancel_url'] = cancel_url
    post_body['emi_option'] = 0
    post_body['cus_name'] = request.user.full_name
    post_body['cus_email'] = request.user.email
    post_body['cus_phone'] = request.user.phone_number
    post_body['cus_add1'] = customer_details.address_line_1
    post_body['cus_city'] = customer_details.city
    post_body['cus_country'] = customer_details.country
    post_body['shipping_method'] = "NO"
    post_body['multi_card_name'] = ""
    post_body['num_of_item'] = 1
    post_body['product_name'] = "Test"
    post_body['product_category'] = "Test Category"
    post_body['product_profile'] = "general"


    response = sslcz.createSession(post_body) # API response
    
    return redirect(response['GatewayPageURL'])

def place_order(request, total=0, quantity=0,):
    current_user = request.user

    # If the cart count is less than or equal to 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") # 20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            
            return render(request, 'orders/payments.html', context)
    else:
        return redirect('checkout')


# def order_complete(request):
#     order_number = request.GET.get('order_number')
#     transID = request.GET.get('payment_id')

#     try:
#         order = Order.objects.get(order_number=order_number, is_ordered=True)
#         ordered_products = OrderProduct.objects.filter(order_id=order.id)

#         subtotal = 0
#         for i in ordered_products:
#             subtotal += i.product_price * i.quantity

#         payment = Payment.objects.get(payment_id=transID)

#         context = {
#             'order': order,
#             'ordered_products': ordered_products,
#             'order_number': order.order_number,
#             'transID': payment.payment_id,
#             'payment': payment,
#             'subtotal': subtotal,
#         }
#         return render(request, 'orders/order_complete.html', context)
#     except (Payment.DoesNotExist, Order.DoesNotExist):
#         return redirect('home')