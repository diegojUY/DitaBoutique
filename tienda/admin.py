from django.contrib import admin
from tienda.models import Adquirido, Producto, Joya, Subscriber, ProductoImagen, JoyaImagen

class AdquiridoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'user', 'ciudad', 'pais', 'total', 'created_at')
    search_fields = ('nombre', 'pais', 'user__username')
    list_filter = ('ciudad', 'pais', 'created_at')
    ordering = ('-created_at',)

class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagen
    extra = 1

class JoyaImagenInline(admin.TabularInline):
    model = JoyaImagen
    extra = 1

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'cantidad', 'categoria', 'temporada_invierno')
    search_fields = ('nombre',)
    list_filter = ('categoria', 'temporada_invierno', 'cantidad')
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
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Joya, JoyaAdmin)
admin.site.register(Subscriber, SubscriberAdmin)