from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from billing.models import SubscriptionPlan
from .services import create_checkout_session


class PurchaseCustomerPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_slug = request.data.get("plan_slug")

        plan = SubscriptionPlan.objects.get(slug=plan_slug)

        session = create_checkout_session(request.user, plan)

        return Response({
            "redirect_url": session.url
        })