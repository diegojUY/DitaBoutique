from django.contrib import admin
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
    list_display = ('numero_orden', 'user', 'nombre', 'total', 'created_at')
    search_fields = ('numero_orden', 'nombre', 'user__username')
    list_filter = ('created_at', 'pais')
    ordering = ('-created_at',)
    inlines = [OrdenCompraItemInline]

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