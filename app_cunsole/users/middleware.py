# import jwt
# from django.conf import settings
# from django.contrib.sessions.middleware import SessionMiddleware
# from django.utils.functional import SimpleLazyObject
# from users.models import User
# from app_cunsole.customer.models import Account


# class JWTSessionMiddleware(SessionMiddleware):
#     def process_request(self, request):
#         # Initialize request attributes
#         request.user = SimpleLazyObject(lambda: None)
#         request.user_account = None
#         request.user_is_authenticated = False

#         # Retrieve the JWT token from the Authorization header
#         header = request.headers.get("Authorization")

#         if header and header.startswith("Bearer "):
#             token = header.split(" ")[1]

#             try:
#                 payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#                 user_id = payload["user_id"]
#                 user = User.objects.get(id=user_id)
#                 request.user = user  # Set the user object in request
#                 request.user_account = user.Account
#                 request.user_is_authenticated = True  # Set user as authenticated

#             except jwt.ExpiredSignatureError:
#                 # Handle token expiration
#                 pass
#             except (jwt.InvalidTokenError, User.DoesNotExist):
#                 # Handle other token errors or user not found
#                 pass

#         super().process_request(request)


# def get_user(request):
#     print(request)
#     print(request.user)
#     return getattr(request, "user", None)


# previus

# import jwt
# from django.conf import settings
# from django.contrib.auth import get_user_model
# from django.contrib.sessions.middleware import SessionMiddleware
# from django.utils.functional import SimpleLazyObject

# User = get_user_model()

# def get_user_from_token(request):
#     header = request.headers.get("Authorization")
#     if header and header.startswith("Bearer "):
#         token = header.split(" ")[1]
#         try:
#             payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#             user_id = payload["user_id"]
#             return User.objects.get(id=user_id)
#         except jwt.ExpiredSignatureError:
#             # Handle token expiration
#             pass
#         except (jwt.InvalidTokenError, User.DoesNotExist):
#             # Handle other token errors or user not found
#             pass
#     return None

# class JWTSessionMiddleware(SessionMiddleware):
#     def process_request(self, request):
#         request.user = SimpleLazyObject(lambda: get_user_from_token(request))
#         super().process_request(request)

#     def process_response(self, request, response):
#         if hasattr(request, 'user'):
#             request.user_account = getattr(request.user, 'account', None)
#             request.user_is_authenticated = request.user.is_authenticated
#         return super().process_response(request, response)


import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import JsonResponse
from django.utils.functional import SimpleLazyObject

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
        request.user_is_authenticated = getattr(request.user, "is_authenticated", False)
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
        return super().process_response(request, response)

    def process_exception(self, request, exception):
        # Optional: Handle exceptions and log errors
        if isinstance(exception, jwt.ExpiredSignatureError):
            return JsonResponse({"error": "Token is expired"}, status=401)
        elif isinstance(exception, jwt.InvalidTokenError):
            return JsonResponse({"error": "Invalid token"}, status=401)
        return super().process_exception(request, exception)
