from typing import Any, Sequence

from django.contrib.auth import get_user_model
from factory import Faker, SubFactory, post_generation
from factory.django import DjangoModelFactory

from editors.users.models import Community, Project


class UserFactory(DjangoModelFactory):

    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]


class CommunityFactory(DjangoModelFactory):
    name = Faker("company")
    owner = SubFactory(UserFactory)

    class Meta:
        model = Community


class ProjectFactory(DjangoModelFactory):
    community = SubFactory(CommunityFactory)
    title = Faker("catch_phrase")
    description = Faker("bs")
    reward = 200

    class Meta:
        model = Project
