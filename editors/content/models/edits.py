from django.db import models
from django.utils.translation import gettext_lazy as _


class Edit(models.Model):
    """Finished edits for a project"""

    class EditStatus(models.IntegerChoices):
        PENDING = 0, _("Pending")
        APPROVED = 1, _("Approved")
        REJECTED = 2, _("Rejected")

    project = models.ForeignKey("users.Project", on_delete=models.CASCADE)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    status = models.PositiveSmallIntegerField(choices=EditStatus.choices)
    video = models.FileField()
