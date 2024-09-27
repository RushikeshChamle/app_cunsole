from django.urls import path

from .views import CustomTokenObtainPairView

# from .views import TokenRefreshView
from .views import create_account
from .views import create_user
from .views import signup
from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view, get_accounts_and_users

app_name = "users"


urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<int:pk>/", view=user_detail_view, name="detail"),
    path("signup/", signup, name="signup"),
    path("create_user/", create_user, name="create_user"),
    path("create_account/", create_account, name="create_account"),
    path("signin/", CustomTokenObtainPairView.as_view(), name="signin"),
    path('accounts_users/', get_accounts_and_users, name='accounts_users'),

    # path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
