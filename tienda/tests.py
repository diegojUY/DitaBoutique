from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from .admin import OrdenCompraAdmin
from .models import Adquirido, OrdenCompra, Producto


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

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Adquirido.objects.filter(user=user).count(), 1)
        self.assertEqual(OrdenCompra.objects.filter(user=user).count(), 1)

        compra = OrdenCompra.objects.get(user=user)
        self.assertTrue(compra.numero_orden.startswith('OC-'))
        self.assertEqual(compra.total, 200)
        self.assertEqual(compra.estado_orden, 'pendiente')
        self.assertEqual(compra.metodo_pago, '')
        self.assertFalse(compra.pago_notificado)
        self.assertEqual(compra.items.count(), 1)
        self.assertEqual(compra.items.first().nombre_producto, 'Aro')

        producto.refresh_from_db()
        self.assertEqual(producto.cantidad, 3)

    def test_actualizar_metodo_pago_guarda_en_orden(self):
        user = User.objects.create_user(username='cliente2', password='123456')
        self.client.login(username='cliente2', password='123456')

        compra = OrdenCompra.objects.create(
            user=user,
            nombre='Cliente Dos',
            domicilio='Calle 1',
            ciudad='Montevideo',
            estado='Montevideo',
            pais='Uruguay',
            total='150.00',
        )

        response = self.client.post(
            reverse('actualizar_metodo_pago', args=[compra.numero_orden]),
            {'method': 'transferencia'},
        )

        self.assertEqual(response.status_code, 200)
        compra.refresh_from_db()
        self.assertEqual(compra.metodo_pago, 'transferencia')

    @patch('tienda.admin.send_mail', return_value=1)
    def test_admin_notifica_pago_confirmado_una_vez(self, mock_send_mail):
        user = User.objects.create_user(username='cliente3', password='123456', email='cliente3@example.com')
        compra = OrdenCompra.objects.create(
            user=user,
            nombre='Cliente Tres',
            domicilio='Calle 2',
            ciudad='Montevideo',
            estado='Montevideo',
            pais='Uruguay',
            total='250.00',
        )

        admin_instance = OrdenCompraAdmin(OrdenCompra, AdminSite())
        compra.estado_orden = 'pagada'
        admin_instance.notificar_pago_si_corresponde(None, compra, 'pendiente')

        compra.refresh_from_db()
        self.assertTrue(compra.pago_notificado)
        self.assertEqual(mock_send_mail.call_count, 1)
