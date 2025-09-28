import datetime

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')
        path = request.path
        user = request.user if request.user.is_authenticated else "Anonymous"
        print(f"[{datetime.datetime.now()}] {user} from {ip} visited {path}")
        response = self.get_response(request)
        return response
