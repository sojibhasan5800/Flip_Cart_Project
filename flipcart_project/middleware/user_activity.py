class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # ✅ Safe check
        if getattr(request, "resolver_match", None):
            view_name = request.resolver_match.view_name

            # শুধু checkout, order, login track করবো
            if view_name in ["checkout", "order_detail", "login"]:
                user = request.user if request.user.is_authenticated else "Anonymous"
                print(f"[UserActivity] {user} visited {view_name}")
        return response