import jwt
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.functional import SimpleLazyObject
from users.models import User


class JWTSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        # Initialize request attributes
        request.user = SimpleLazyObject(lambda: None)
        request.user_account = None
        request.user_is_authenticated = False

        # Retrieve the JWT token from the Authorization header
        header = request.headers.get("Authorization")

        if header and header.startswith("Bearer "):
            token = header.split(" ")[1]

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = payload["user_id"]
                user = User.objects.get(id=user_id)
                request.user = user  # Set the user object in request
                request.user_account = user.Account
                request.user_is_authenticated = True  # Set user as authenticated

            except jwt.ExpiredSignatureError:
                # Handle token expiration
                pass
            except (jwt.InvalidTokenError, User.DoesNotExist):
                # Handle other token errors or user not found
                pass

        super().process_request(request)


def get_user(request):
    print(request)
    print(request.user)
    return getattr(request, "user", None)
