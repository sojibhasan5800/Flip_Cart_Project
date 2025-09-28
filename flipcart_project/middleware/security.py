from django.http import JsonResponse
import time

RATE_LIMIT = {}
LIMIT = 5   # one mintutes request highly five time
WINDOW = 60 # 60 seconds

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')
        now = time.time()

        if ip not in RATE_LIMIT:
            RATE_LIMIT[ip] = []
        
        # cancel the previous request
        RATE_LIMIT[ip] = [t for t in RATE_LIMIT[ip] if now - t < WINDOW]

        if len(RATE_LIMIT[ip]) >= LIMIT:
            return JsonResponse({"error": "Too many requests. Try again later."}, status=429)

        RATE_LIMIT[ip].append(now)
        response = self.get_response(request)
        return response
