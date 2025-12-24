from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class PublicAdminCheckAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "is_public_admin": getattr(request, "is_public_admin", False),
            "user": request.user.email
        })
