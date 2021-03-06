import datetime as dt

from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ParseError, PermissionDenied
from rest_framework.response import Response
from rest_framework.serializers import CharField, ModelSerializer
from rest_framework.viewsets import ModelViewSet

from editors.content.models import Edit
from editors.users.models import Community, Project, ProjectVideo


class CommunitySerializer(ModelSerializer):
    class Meta:
        model = Community
        fields = "__all__"


class ProjectSerializer(ModelSerializer):
    community_name = CharField(source="community.name", read_only=True)

    class Meta:
        model = Project
        fields = "__all__"


class ProjectVideoSerializer(ModelSerializer):
    class Meta:
        model = ProjectVideo
        fields = "__all__"


class EditSerializer(ModelSerializer):
    class Meta:
        model = Edit
        fields = "__all__"


class ListMixin(ModelViewSet):
    def get_stuff(self, qs, serializer=None):
        if serializer is None:
            serializer = self.get_serializer_class()
        queryset = self.filter_queryset(qs)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer(
                page, many=True, context=self.get_serializer_context()
            )
            return self.get_paginated_response(serializer.data)

        serializer = serializer(
            queryset, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)


class CommunityViewSet(ListMixin):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer

    @action(methods=["GET"], detail=True)
    def projects(self, request, pk=None):
        return self.get_stuff(
            Project.objects.filter(community_id=pk), ProjectSerializer
        )


class ProjectViewSet(ListMixin):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def list(self, request, *args, **kwargs):
        return self.get_stuff(
            Project.objects.filter(
                Q(lock_expire__isnull=True) | Q(lock_expire__lte=timezone.now())
            ).order_by("-lock_expire")
        )

    @action(methods=["GET"], detail=False)
    def my_projects(self, request):
        return self.get_stuff(
            Project.objects.filter(community__owner=request.user),
        )

    @action(methods=["POST"], detail=False)
    def claim(self, request):
        try:
            project = Project.objects.get(id=request.data["project_id"])
        except Project.DoesNotExist:
            raise NotFound("Must include project_id in JSON body")
        if project.lock_expire and project.lock_expire > timezone.now():
            raise PermissionDenied("Someone else has already claimed this job")
        project.lock_user = request.user
        project.lock_expire = timezone.now() + dt.timedelta(days=7)
        project.save(update_fields=["lock_user", "lock_expire"])
        return Response(status=201)

    @action(methods=["GET"], detail=False)
    def mine(self, request):
        return self.get_stuff(
            Project.objects.filter(
                lock_user=request.user, lock_expire__gte=timezone.now()
            ),
        )


class ProjectVideoViewSet(ModelViewSet):
    serializer_class = ProjectVideoSerializer

    def get_queryset(self):
        if "project" not in self.request.query_params:
            raise ParseError(
                'Must include "project" (i.e. project id) in query parameters'
            )
        return ProjectVideo.objects.filter(
            project_id=self.request.query_params["project"]
        ).order_by("-id")


class EditViewSet(ListMixin):
    serializer_class = EditSerializer

    def get_queryset(self):
        if "project" not in self.request.query_params:
            raise ParseError(
                'Must include "project" (i.e. project id) in query parameters'
            )

        return Edit.objects.filter(
            project_id=self.request.query_params["project"]
        ).order_by("-id")

    @action(methods=["GET"], detail=False)
    def mine(self, request):
        return self.get_stuff(
            Edit.objects.filter(user=request.user).order_by("-id"),
        )

    @action(methods=["POST"], detail=False)
    def handle(self, request):
        try:
            project = Project.objects.get(id=request.data["project_id"])
            assert (
                project.community.owner.is_superuser
                or project.community.owner == request.user
            )
        except (Project.DoesNotExist, AssertionError):
            raise PermissionDenied
        except KeyError:
            raise ParseError('Must include "project_id" (i.e. project id) in JSON body')

        # Pending 0
        # Approve 1
        # No 2
        try:
            edit = Edit.objects.get(id=request.data["edit_id"])
        except Edit.DoesNotExist:
            raise NotFound("Edit id does not exist")
        Edit.objects.filter(id=request.data["edit_id"]).update(
            status=request.data["status"]
        )
        project.video = edit.video
        project.save(update_fields=["video"])
        return Response(status=201)
