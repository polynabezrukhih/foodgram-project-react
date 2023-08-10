from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet


class CustomMixin(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    pass
