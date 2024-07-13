from rest_framework import serializers
from rest_framework.authtoken.admin import User

from user.models import Ingresso


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'cpf',
            'email',
            'tipo',
            'is_primeiro_acesso'
        ]


class IngressoSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)

    class Meta:
        model = Ingresso
        fields = [
            'id',
            'usuario',
            'created_at',
            'utilizado_em'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'utilizado_em': {'read_only': True},
        }

    def create(self, validated_data):
        validated_data['usuario'] = self.context['request'].user
        return Ingresso.objects.create(**validated_data)



class ValidateIngressoSerializer(serializers.Serializer):
    ingresso = serializers.UUIDField(required=True)
