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


class CommunityViewSet(ModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer

    @action(methods=["GET"], detail=True)
    def projects(self, request, pk=None):
        queryset = self.filter_queryset(Project.objects.filter(community_id=pk))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProjectSerializer(
                page, many=True, **self.get_serializer_context()
            )
            return self.get_paginated_response(serializer.data)

        serializer = ProjectSerializer(
            queryset, many=True, **self.get_serializer_context()
        )
        return Response(serializer.data)


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.filter(
        Q(lock_expire__isnull=False) | Q(lock_expire__lte=timezone.now())
    ).order_by("-lock_expire")
    serializer_class = ProjectSerializer

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
        queryset = self.filter_queryset(
            Project.objects.filter(
                lock_user=request.user, lock_expire__gte=timezone.now()
            )
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


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


class EditViewSet(ModelViewSet):
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
        queryset = self.filter_queryset(
            Edit.objects.filter(user=request.user).order_by("-id")
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
        project.save()
        return Response()
