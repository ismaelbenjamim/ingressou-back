from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import get_random_string

from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.admin import User
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from user.apis.serializers import UserSerializer, IngressoSerializer, ValidateIngressoSerializer, LoginSerializer, \
    EsqueciSenhaSerializer, RedefinirSenhaSerializer, PagamentoSerializer, ValidateCpfSerializer, \
    GenerateIngressoSerializer, FirstAccessSerializer, PaymentIngressoSerializer, MeusIngressosSerializer
from user.filters import UserFilter
from user.gerar_qrcode import gerar_qr_code_base64
from user.models import Ingresso, UserType, Pagamento


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    filterset_class = UserFilter

    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':  # Allow unauthenticated GET requests
            return [AllowAny()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        if self.request.user.tipo == UserType.COMUM:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[],
            serializer_class=ValidateCpfSerializer, url_path='validate_cpf/(?P<cpf>[^/.]+)')
    def validate_cpf(self, request, cpf, *args, **kwargs):
        serializer = ValidateCpfSerializer(data={
            "cpf": cpf
        })
        if serializer.is_valid():
            cpf = serializer.validated_data['cpf']
            user = get_object_or_404(User, cpf=cpf)
            return Response({
                "primeiro_acesso": user.is_primeiro_acesso
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[], serializer_class=LoginSerializer)
    def login(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            cpf = serializer.validated_data['cpf']
            password = serializer.validated_data['password']

            user = authenticate(request, username=cpf, password=password)

            if user is not None:
                if not user.is_active:
                    return Response({'error': 'User is inactive.'}, status=status.HTTP_400_BAD_REQUEST)

                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'tipo': user.tipo
                })

            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[], serializer_class=FirstAccessSerializer)
    def primeiro_acesso(self, request, *args, **kwargs):
        serializer = FirstAccessSerializer(data=request.data)
        if serializer.is_valid():
            cpf = serializer.validated_data['cpf']
            password = serializer.validated_data['password']
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(cpf=cpf)
                if not user.is_primeiro_acesso:
                    return Response({'error': 'Senha já definida'}, status=status.HTTP_400_BAD_REQUEST)

                user.password = make_password(password)
                user.is_primeiro_acesso = False
                user.email = email
                user.save()
                return Response({'success': 'dados definidos com sucesso'})

            except User.DoesNotExist:
                return Response({'error': 'usuário não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[])
    def esqueci_senha(self, request, *args, **kwargs):
        serializer = EsqueciSenhaSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(cpf=serializer.validated_data['cpf'])

                temp_password = get_random_string(length=8)
                user.password = make_password(temp_password)
                user.is_primeiro_acesso = True
                user.save()

                send_mail(
                    'Redefinição de senha ingressou',
                    f'Sua nova senha temporária é: {temp_password}. Por favor, altere-a no primeiro acesso.',
                    'ingressou.olas@gmail.com',
                    [user.email],
                    fail_silently=False,
                )
                return Response({'success': 'E-mail com senha temporária enviado'})


            except User.DoesNotExist:
                return Response({'error': 'usuário não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def redefinir_senha(self, request, *args, **kwargs):
        serializer = RedefinirSenhaSerializer(data=request.data)

        if serializer.is_valid():
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']

            user = request.user

            if not user.check_password(old_password):
                return Response({'error': 'Senha antiga incorreta'}, status=status.HTTP_400_BAD_REQUEST)

            user.password = make_password(new_password)
            user.save()
            return Response({'success': 'Senha redefinida com sucesso'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def redefinir_senha(self, request, *args, **kwargs):
        serializer = RedefinirSenhaSerializer(data=request.data)

        if serializer.is_valid():
            pass


class IngressoViewSet(viewsets.ModelViewSet):
    queryset = Ingresso.objects.all()
    serializer_class = IngressoSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'put', 'delete']

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

    @action(detail=False, methods=['post'], serializer_class=GenerateIngressoSerializer)
    def generate(self, request):
        if self.request.user.tipo == UserType.COMUM:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ingresso = serializer.create(serializer.validated_data)
        response = IngressoSerializer(instance=ingresso)
        return Response(response.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], serializer_class=PaymentIngressoSerializer)
    def payment(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ingressos_pk = serializer.create(serializer.validated_data)
        response = IngressoSerializer(many=True, instance=Ingresso.objects.filter(pk__in=ingressos_pk))
        return Response(response.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], serializer_class=MeusIngressosSerializer)
    def meus_ingressos(self, request):
        ingressos = Ingresso.objects.filter(usuario=self.request.user)
        data = {
            "ingressos": [gerar_qr_code_base64(ingresso.pk) for ingresso in ingressos]
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class PagamentoViewSet(viewsets.ModelViewSet):
    serializer_class = PagamentoSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get']

    def get_queryset(self):
        return Pagamento.objects.all().order_by('-created_at')[:1]
