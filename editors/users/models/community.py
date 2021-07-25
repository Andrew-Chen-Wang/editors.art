from django.db import models


class Community(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey("users.User", on_delete=models.CASCADE)


class Project(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    lock_expire = models.DateTimeField(null=True)
    lock_user = models.ForeignKey("users.User", on_delete=models.CASCADE, null=True)
    description = models.TextField(max_length=3000)
    reward = models.PositiveIntegerField(default=0)
    hidden = models.BooleanField(default=False)
    last_post = models.DateTimeField(null=True, blank=True)
    video = models.FileField(blank=True)


class ProjectVideo(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    video = models.FileField()
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(max_length=2000, blank=True)
