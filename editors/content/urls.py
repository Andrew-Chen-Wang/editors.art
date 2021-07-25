from rest_framework.routers import DefaultRouter

from editors.content.views import (
    CommunityViewSet,
    EditViewSet,
    ProjectVideoViewSet,
    ProjectViewSet,
)

router = DefaultRouter()
router.register("project", viewset=ProjectViewSet, basename="project")
router.register("community", viewset=CommunityViewSet, basename="community")
router.register("project-video", viewset=ProjectVideoViewSet, basename="project-video")
router.register("edit", viewset=EditViewSet, basename="edit")


app_name = "content"
urlpatterns = [] + router.urls
