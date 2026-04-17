from django.test import TestCase
from django.urls import reverse
from .models import Adquirido, Producto


class TiendaSmokeTests(TestCase):
    def test_root_url_returns_index(self):
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_adquirido_str_returns_nombre(self):
        adquirido = Adquirido.objects.create(
            nombre='Prueba',
            domicilio='Av. Principal 123',
            ciudad='Montevideo',
            estado='RM',
            pais='Uruguay',
            sitioweb='https://example.com',
        )
        self.assertEqual(str(adquirido), 'Prueba')

    def test_producto_str_returns_nombre(self):
        producto = Producto.objects.create(
            nombre='Bolso',
            precio='1590.00',
            portada='banners/hero.jpg',
        )
        self.assertEqual(str(producto), 'Bolso')
