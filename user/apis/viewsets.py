from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.admin import User
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from user.apis.serializers import UserSerializer, IngressoSerializer, ValidateIngressoSerializer
from user.models import Ingresso, UserType


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'put']
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        if self.request.user.tipo == UserType.COMUM:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        if self.request.user.tipo == UserType.COMUM:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return super().list(request, *args, **kwargs)


class IngressoViewSet(viewsets.ModelViewSet):
    queryset = Ingresso.objects.all()
    serializer_class = IngressoSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post']

    def get_queryset(self):
        return self.request.user.ingressos.all()

    @action(detail=False, methods=['post'], serializer_class=ValidateIngressoSerializer)
    def validate(self, request):
        if self.request.user.tipo == UserType.COMUM:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ingresso_id = serializer.validated_data['ingresso']
        ingresso = get_object_or_404(Ingresso, id=ingresso_id)

        if ingresso.utilizado_em:
            return Response({"msg": "Ingresso já utilizado"}, status=status.HTTP_400_BAD_REQUEST)

        ingresso.utilizado_em = timezone.now()
        ingresso.save()

        return Response({"msg": "Ingresso autorizado"}, status=status.HTTP_200_OK)

