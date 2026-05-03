from django.contrib import admin, messages
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
    list_display = ('numero_orden', 'user', 'nombre', 'estado_orden', 'metodo_pago', 'total', 'created_at', 'acciones_estado')
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
                botones.append(format_html('<strong>{}</strong>', label))
                continue
            url = reverse('admin:tienda_ordencompra_cambiar_estado', args=[obj.pk, estado])
            botones.append(format_html('<a class="button" href="{}">{}</a>', url, label))
        return format_html(' '.join(['{}'] * len(botones)), *botones)

    acciones_estado.short_description = 'Acciones'

    def cambiar_estado_view(self, request, orden_id, nuevo_estado):
        estados_validos = {'pendiente', 'pagada', 'cancelada'}
        if nuevo_estado not in estados_validos:
            self.message_user(request, 'Estado de orden invalido.', level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:tienda_ordencompra_changelist'))

        orden = self.get_object(request, orden_id)
        if orden is None:
            self.message_user(request, 'La orden no existe.', level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:tienda_ordencompra_changelist'))

        orden.estado_orden = nuevo_estado
        orden.save(update_fields=['estado_orden'])
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