from django.contrib import admin

from user.models import Usuario, Ingresso, Pagamento


# Register your models here.

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('cpf', 'email', 'tipo')


@admin.register(Ingresso)
class IngressoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'created_at')


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('chave', 'valor')
