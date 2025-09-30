class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        #  request phase
        resolver_match = getattr(request, "resolver_match", None)
        view_name = resolver_match.view_name if resolver_match else None

        # response তরি
        response = self.get_response(request)

        #   response after work
        if view_name in ["checkout", "order_detail", "login"]:
            user = request.user if request.user.is_authenticated else "Anonymous"
            print(f"[SECURITY] {user} accessed {view_name}")

        return response
