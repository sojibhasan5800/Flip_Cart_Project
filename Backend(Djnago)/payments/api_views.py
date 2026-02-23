from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
import stripe
import requests  # For bKash API
from django.utils import timezone
from .models import PaymentTransaction
from billing.models import OrganizationSubscription
from .serializers import PaymentTransactionSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreatePaymentIntent(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        gateway = request.data.get('gateway')
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'USD')
        boost_product_id = request.data.get('boost_product_id')  # If for boost
        stripe_token = request.data.get('stripe_token')  # For Stripe charge if needed

        org = request.user.merchant_profile.first().organization
        sub = OrganizationSubscription.objects.filter(organization=org, status='active').first()  # Assume one active sub

        if boost_product_id and (not sub or not sub.can_boost_more()):
            return Response({"error": "No active plan or boost limit reached. Purchase/upgrade plan first."}, status=status.HTTP_400_BAD_REQUEST)

        trans = PaymentTransaction.objects.create(
            organization=org,
            subscription=sub,
            amount=amount,
            currency=currency,
            gateway=gateway,
            metadata={'boost_product_id': boost_product_id} if boost_product_id else {}
        )

        try:
            if gateway == 'stripe':
                # Create PaymentIntent
                intent = stripe.PaymentIntent.create(
                    amount=int(amount * 100),
                    currency=currency.lower(),
                    description="Product Boost" if boost_product_id else "Subscription Payment",
                    customer=org.stripe_customer_id,
                )
                trans.gateway_transaction_id = intent.id
                trans.save()
                return Response({"client_secret": intent.client_secret})

            elif gateway == 'bkash':
                # bKash create payment session
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self._get_bkash_token()}',
                    'x-app-key': settings.BKASH_APP_KEY
                }
                payload = {
                    'mode': '0011',  # Checkout
                    'amount': str(amount),
                    'currency': 'BDT',
                    'intent': 'sale',
                    'payerReference': org.business_email,
                    'merchantInvoiceNumber': trans.transaction_id,
                    'callbackURL': settings.BKASH_SUCCESS_CALLBACK  # Webhook-like
                }
                res = requests.post(f'{settings.BKASH_BASE_URL}/create', json=payload, headers=headers)
                bkash_data = res.json()
                if bkash_data.get('statusCode') != '0000':
                    raise Exception(bkash_data.get('statusMessage'))
                
                trans.gateway_transaction_id = bkash_data['paymentID']
                trans.save()
                return Response({"bkash_url": bkash_data['bkashURL']})

        except Exception as e:
            trans.status = 'failed'
            trans.save()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _get_bkash_token(self):
        # bKash token grant
        payload = {
            'app_key': settings.BKASH_APP_KEY,
            'app_secret': settings.BKASH_APP_SECRET
        }
        headers = {
            'username': settings.BKASH_USERNAME,
            'password': settings.BKASH_PASSWORD,
            'Content-Type': 'application/json'
        }
        res = requests.post(f'{settings.BKASH_BASE_URL}/token/grant', json=payload, headers=headers)
        return res.json()['id_token']

class PaymentWebhook(APIView):
    def post(self, request):
        # Stripe webhook
        if 'stripe' in request.data:
            event = stripe.Event.construct_from(request.data, stripe.api_key)
            if event.type == 'payment_intent.succeeded':
                trans = PaymentTransaction.objects.get(gateway_transaction_id=event.data.object.id)
                trans.status = 'success'
                trans.verify_and_complete()
            # Handle other events...

        # bKash callback (from callbackURL)
        elif 'bkash' in request.data:
            payment_id = request.data.get('paymentID')
            trans = PaymentTransaction.objects.get(gateway_transaction_id=payment_id)
            # Verify with bKash query API
            headers = {'Authorization': f'Bearer {self._get_bkash_token()}', 'x-app-key': settings.BKASH_APP_KEY}
            res = requests.post(f'{settings.BKASH_BASE_URL}/query', json={'paymentID': payment_id}, headers=headers)
            bkash_res = res.json()
            if bkash_res['transactionStatus'] == 'Completed':
                trans.status = 'success'
                trans.verify_and_complete()
            else:
                trans.status = 'failed'
            trans.save()

        return Response(status=status.HTTP_200_OK)

class RefundPayment(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trans_id):
        trans = get_object_or_404(PaymentTransaction, id=trans_id, organization=request.user.merchant_profile.first().organization)
        if trans.status != 'success':
            return Response({"error": "Cannot refund non-successful payment"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if trans.gateway == 'stripe':
                refund = stripe.Refund.create(charge=trans.gateway_transaction_id)
            elif trans.gateway == 'bkash':
                # bKash refund API
                headers = {'Authorization': f'Bearer {self._get_bkash_token()}', 'x-app-key': settings.BKASH_APP_KEY}
                payload = {'paymentID': trans.gateway_transaction_id, 'amount': str(trans.amount), 'sku': 'refund'}
                res = requests.post(f'{settings.BKASH_BASE_URL}/refund', json=payload, headers=headers)
                if res.json()['statusCode'] != '0000':
                    raise Exception('Refund failed')

            trans.status = 'refunded'
            trans.save()
            # Reverse boost if applicable
            if trans.boost:
                trans.boost.is_active = False
                trans.boost.save()
            return Response({"message": "Refund processed"})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)