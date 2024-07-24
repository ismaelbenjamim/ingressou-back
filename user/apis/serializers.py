from rest_framework import serializers
from rest_framework.authtoken.admin import User

from user.models import Ingresso, Pagamento


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'cpf',
            'email',
            'tipo',
            'birthday',
            'is_primeiro_acesso'
        ]


class IngressoSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    situacao = serializers.CharField(required=True)

    class Meta:
        model = Ingresso
        fields = [
            'id',
            'usuario',
            'nome',
            'data_nascimento',
            'situacao',
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


class GenerateIngressoSerializer(serializers.Serializer):
    usuario = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='cpf', required=True)
    nome = serializers.CharField(required=True)
    data_nascimento = serializers.DateField(required=True)
    situacao = serializers.CharField(required=True)

    def create(self, validated_data):
        return Ingresso.objects.create(**validated_data)


class UserIngressoSerializer(serializers.Serializer):
    nome = serializers.CharField(required=True)
    data_nascimento = serializers.DateField(required=True)
    situacao = serializers.CharField(required=True)


class PaymentIngressoSerializer(serializers.Serializer):
    ingressos = UserIngressoSerializer(many=True)

    def create(self, validated_data):
        ingressos = []
        for ingresso_data in validated_data['ingressos']:
            ingresso_data['usuario'] = self.context['request'].user
            ingresso = Ingresso.objects.create(**ingresso_data)
            ingressos.append(ingresso.pk)
        return ingressos


class MeusIngressosSerializer(serializers.Serializer):
    ingressos = serializers.ListField()


class LoginSerializer(serializers.Serializer):
    cpf = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class ValidateCpfSerializer(serializers.Serializer):
    cpf = serializers.CharField(required=True, write_only=True)
    primeiro_acesso = serializers.BooleanField(read_only=True, default=True)


class FirstAccessSerializer(serializers.Serializer):
    cpf = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    email = serializers.CharField(required=True)


class EsqueciSenhaSerializer(serializers.Serializer):
    cpf = serializers.CharField(required=True)


class RedefinirSenhaSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class PagamentoSerializer(serializers.Serializer):
    class Meta:
        model = Pagamento
        fields = ['chave', 'valor']
