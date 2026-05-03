from django.conf import settings
from django.contrib import admin, messages
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from tienda.models import Adquirido, Joya, JoyaImagen, OrdenCompra, OrdenCompraItem, Producto, ProductoImagen, Subscriber

class AdquiridoAdmin(admin.ModelAdmin):
    list_display = ('numero_orden', 'nombre', 'user', 'ciudad', 'pais', 'total', 'created_at')
    search_fields = ('numero_orden', 'nombre', 'pais', 'user__username')
    list_filter = ('ciudad', 'pais', 'created_at')
    ordering = ('-created_at',)


class OrdenCompraItemInline(admin.TabularInline):
    model = OrdenCompraItem
    extra = 0
    readonly_fields = ('nombre_producto', 'tipo_producto', 'cantidad', 'precio_unitario', 'subtotal')


class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ('numero_orden', 'user', 'nombre', 'estado_badge', 'metodo_pago', 'total', 'created_at', 'acciones_estado')
    search_fields = ('numero_orden', 'nombre', 'user__username')
    list_filter = ('created_at', 'pais', 'estado_orden', 'metodo_pago')
    ordering = ('-created_at',)
    inlines = [OrdenCompraItemInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:orden_id>/estado/<str:nuevo_estado>/',
                self.admin_site.admin_view(self.cambiar_estado_view),
                name='tienda_ordencompra_cambiar_estado',
            ),
        ]
        return custom_urls + urls

    def acciones_estado(self, obj):
        botones = []
        for estado, label in (('pendiente', 'Pendiente'), ('pagada', 'Pagada'), ('cancelada', 'Cancelada')):
            if obj.estado_orden == estado:
                botones.append(format_html('<span style="font-weight:700;">{}</span>', label))
                continue
            url = reverse('admin:tienda_ordencompra_cambiar_estado', args=[obj.pk, estado])
            botones.append(format_html('<a class="button" href="{}">{}</a>', url, label))
        return format_html(' '.join(['{}'] * len(botones)), *botones)

    acciones_estado.short_description = 'Acciones'

    def estado_badge(self, obj):
        colors = {
            'pendiente': ('#7a5d00', '#fff4cc'),
            'pagada': ('#13653f', '#daf5e7'),
            'cancelada': ('#8d1f1f', '#fde0e0'),
        }
        color, background = colors.get(obj.estado_orden, ('#222222', '#efefef'))
        return format_html(
            '<span style="display:inline-flex; padding:4px 10px; border-radius:999px; font-weight:700; color:{}; background:{};">{}</span>',
            color,
            background,
            obj.get_estado_orden_display(),
        )

    estado_badge.short_description = 'Estado'

    def save_model(self, request, obj, form, change):
        previous_estado = None
        if change:
            previous_estado = OrdenCompra.objects.filter(pk=obj.pk).values_list('estado_orden', flat=True).first()

        super().save_model(request, obj, form, change)
        self.notificar_pago_si_corresponde(request, obj, previous_estado)

    def notificar_pago_si_corresponde(self, request, orden, previous_estado):
        if orden.estado_orden != 'pagada' or orden.pago_notificado:
            return

        if previous_estado == 'pagada':
            return

        email = getattr(orden.user, 'email', '') or ''
        if not email:
            if request is not None:
                self.message_user(request, 'La orden se marco como pagada, pero el usuario no tiene email cargado.', level=messages.WARNING)
            return

        metodo = orden.get_metodo_pago_display() or 'Sin seleccionar'
        sent = send_mail(
            f'Pago confirmado - {orden.numero_orden}',
            (
                f'Hola {orden.nombre},\n\n'
                f'Tu orden {orden.numero_orden} fue marcada como pagada.\n'
                f'Metodo de pago: {metodo}.\n'
                f'Total: ${orden.total}.\n\n'
                'Gracias por comprar en DitaBoutique.'
            ),
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=True,
        )
        if sent:
            orden.pago_notificado = True
            orden.save(update_fields=['pago_notificado'])
            if request is not None:
                self.message_user(request, f'Se envio el correo de pago confirmado a {email}.')
        elif request is not None:
            self.message_user(request, 'No se pudo enviar el correo de confirmacion. Revisa la configuracion de email.', level=messages.WARNING)

    def cambiar_estado_view(self, request, orden_id, nuevo_estado):
        estados_validos = {'pendiente', 'pagada', 'cancelada'}
        if nuevo_estado not in estados_validos:
            self.message_user(request, 'Estado de orden invalido.', level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:tienda_ordencompra_changelist'))

        orden = self.get_object(request, orden_id)
        if orden is None:
            self.message_user(request, 'La orden no existe.', level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:tienda_ordencompra_changelist'))

        previous_estado = orden.estado_orden
        orden.estado_orden = nuevo_estado
        orden.save(update_fields=['estado_orden'])
        self.notificar_pago_si_corresponde(request, orden, previous_estado)
        self.message_user(request, f'La orden {orden.numero_orden} ahora esta {orden.get_estado_orden_display().lower()}.')

        next_url = request.META.get('HTTP_REFERER') or reverse('admin:tienda_ordencompra_changelist')
        return HttpResponseRedirect(next_url)

class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagen
    extra = 1

class JoyaImagenInline(admin.TabularInline):
    model = JoyaImagen
    extra = 1

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'cantidad', 'categoria')
    search_fields = ('nombre',)
    list_filter = ('categoria', 'cantidad')
    ordering = ('nombre',)
    inlines = [ProductoImagenInline]

class JoyaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'categoria')
    search_fields = ('nombre',)
    list_filter = ('categoria',)
    ordering = ('nombre',)
    inlines = [JoyaImagenInline]

class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre', 'created_at')
    search_fields = ('email', 'nombre')
    ordering = ('-created_at',)

admin.site.register(Adquirido, AdquiridoAdmin)
admin.site.register(OrdenCompra, OrdenCompraAdmin)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Joya, JoyaAdmin)
admin.site.register(Subscriber, SubscriberAdmin)