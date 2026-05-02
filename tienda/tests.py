from django.test import TestCase
from django.contrib.auth.models import User
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
        self.assertTrue(str(adquirido).startswith('Prueba - '))
        self.assertIsNotNone(adquirido.numero_orden)
        self.assertTrue(adquirido.numero_orden.startswith('OC-'))

    def test_producto_str_returns_nombre(self):
        producto = Producto.objects.create(
            nombre='Bolso',
            precio='1590.00',
            portada='banners/hero.jpg',
        )
        self.assertEqual(str(producto), 'Bolso')

    def test_finalizar_compra_creates_order_for_logged_user(self):
        user = User.objects.create_user(username='cliente', password='123456')
        self.client.login(username='cliente', password='123456')

        producto = Producto.objects.create(
            nombre='Aro',
            precio='100.00',
            portada='banners/hero.jpg',
            cantidad=5,
        )

        session = self.client.session
        session['cart'] = {
            str(producto.id): {
                'product_id': producto.id,
                'tipo': 'producto',
                'nombre': producto.nombre,
                'precio': '100.00',
                'cantidad': 2,
                'imagen': '',
            }
        }
        session['cart_count'] = 2
        session.save()

        response = self.client.post(reverse('finalizar_compra'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'carrito.html')
        self.assertEqual(Adquirido.objects.filter(user=user).count(), 1)

        compra = Adquirido.objects.get(user=user)
        self.assertTrue(compra.numero_orden.startswith('OC-'))
        self.assertEqual(compra.total, 200)

        producto.refresh_from_db()
        self.assertEqual(producto.cantidad, 3)
