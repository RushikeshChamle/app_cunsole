import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import JsonResponse
from django.utils.functional import SimpleLazyObject
from django.middleware.csrf import rotate_token

User = get_user_model()

def get_user_from_token(request):
    header = request.headers.get("Authorization")
    if header and header.startswith("Bearer "):
        token = header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if user_id:
                return User.objects.filter(id=user_id).first()
        except jwt.ExpiredSignatureError:
            # Optional: Log token expiration
            return None
        except (jwt.InvalidTokenError, User.DoesNotExist):
            # Optional: Log token error
            return None
    return None

class JWTSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        
        request.user = SimpleLazyObject(lambda: get_user_from_token(request))
        request.user_account = getattr(request.user, "account", None)
        request.user_id = getattr(request.user, "id", None)  # Get user ID
        request.user_is_authenticated = getattr(request.user, "is_authenticated", False)
        print("Middleware User Id:", request.user_id)
        print("Middleware User Account:", request.user_account)
        print("Middleware User Authenticated:", request.user_is_authenticated)
        print("Request User:", request.user.id)
        print("User Account:", request.user.account)


        super().process_request(request)

    def process_response(self, request, response):
        # Ensure user-related attributes are set correctly
        if hasattr(request, "user"):
            request.user_account = getattr(request.user, "account", None)
          
            request.user_is_authenticated = getattr(
                request.user,
                "is_authenticated",
                False,
            )

        # rotate_token(request)
        return super().process_response(request, response)

    def process_exception(self, request, exception):
        # Handle exceptions and return JSON responses directly
        if isinstance(exception, jwt.ExpiredSignatureError):
            return JsonResponse({"error": "Token is expired"}, status=401)
        elif isinstance(exception, jwt.InvalidTokenError):
            return JsonResponse({"error": "Invalid token"}, status=401)
        # Handle any other exceptions
        return JsonResponse({"error": "An unexpected error occurred"}, status=500)


