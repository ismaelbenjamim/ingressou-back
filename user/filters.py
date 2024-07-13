from django_filters import rest_framework as filters

from user.models import Usuario


class UserFilter(filters.FilterSet):
    class Meta:
        model = Usuario
        fields = ['cpf']
