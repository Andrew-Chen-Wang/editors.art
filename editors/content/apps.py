from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ContentConfig(AppConfig):
    name = "editors.content"
    verbose_name = _("Content")

    def ready(self):
        try:
            import editors.content.signals  # noqa F401
        except ImportError:
            pass
