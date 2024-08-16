from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "app_cunsole.users"
    verbose_name = _("Users")

    # def ready(self):
    #     with contextlib.suppress(ImportError):
    #         import app_cunsole.users.signals
