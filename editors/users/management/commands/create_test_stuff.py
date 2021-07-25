import datetime as dt
from random import randint
from typing import Any, Optional

import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now

from editors.users.models import Community, User
from editors.users.tests.factories import CommunityFactory, ProjectFactory

S_V = "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"


class Command(BaseCommand):
    help = "Creates test objects for initial setup in database"

    @property
    def path(self):
        return settings.APPS_DIR / "media" / "sample.mp4"

    def create_video(self):
        (settings.APPS_DIR / "media").mkdir(exist_ok=True)
        if not self.path.is_file():
            r = requests.get(S_V, allow_redirects=True)
            if not r.ok:
                raise CommandError("Could not sample download video")
            self.path.open("wb").write(r.content)

    def create_factory(self, num: int):
        manager = User.objects.create_user(
            f"manager{num}", f"manager{num}@test.com", "test"
        )

        community: Community = CommunityFactory(owner=manager)
        ProjectFactory.create_batch(
            randint(1, 3),
            community=community,
            video="sample.mp4",
            lock_expire=now() + dt.timedelta(days=3),
        )

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        self.stdout.write("Creating admin test, test@test.com, pw: test")
        User.objects.create_superuser("test", "test@test.com", "test")
        self.stdout.write("Creating communities and projects")
        self.create_video()
        for x in range(10):
            self.create_factory(x)

        for user in User.objects.only("id").all():
            user.password = make_password("test")
            user.save()
        self.stdout.write(self.style.SUCCESS("Successfully created data"))
        return
