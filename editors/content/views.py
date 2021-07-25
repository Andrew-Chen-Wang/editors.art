from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from editors.content.models import Edit
from editors.users.models import Community, Project, ProjectVideo


class CommunitySerializer(ModelSerializer):
    class Meta:
        model = Community
        fields = "__all__"


class ProjectSerializer(ModelSerializer):
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


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.filter(lock_expire__isnull=False).order_by(
        "-lock_expire"
    )
    serializer_class = ProjectSerializer


class ProjectVideoViewSet(ModelViewSet):
    serializer_class = ProjectVideoSerializer

    def get_queryset(self):
        return ProjectVideo.objects.filter(
            project_id=self.request.query_params["project"]
        ).order_by("-id")


class EditViewSet(ModelViewSet):
    queryset = Edit.objects.all()
    serializer_class = EditSerializer

    def get_queryset(self):
        return Edit.objects.filter(
            project_id=self.request.query_params["project"]
        ).order_by("-id")
