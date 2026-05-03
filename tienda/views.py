from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import TemplateDoesNotExist
from django.urls import reverse
from django.views.generic import TemplateView
from urllib.parse import quote

from .cart import Cart
from .models import Adquirido, OrdenCompra, OrdenCompraItem, Producto, Joya, Subscriber, UserProfile


PAYMENT_METHODS = {
    'transferencia': {
        'title': 'Transferencia bancaria',
        'lines': [
            'BROU: 110794545-00001',
            'Desde otros bancos: 11079454500001',
            'Tatiana Alvarez',
            'PREX: 391372 Tatiana Alvarez',
            'OCABLUE: 6273135 Diego Jorge',
        ],
    },
    'deposito': {
        'title': 'Depósito',
        'lines': [
            'Podés depositar en cuenta BROU y enviarnos el comprobante para validar tu pago.',
        ],
    },
    'efectivo': {
        'title': 'Efectivo al coordinar envío',
        'lines': [
            'Coordinamos contigo el envío y abonás en efectivo al momento de la entrega.',
        ],
    },
    'abitab': {
        'title': 'Giro por Abitab',
        'lines': [
            'Te compartimos los datos de destinatario por WhatsApp cuando confirmes este método.',
        ],
    },
    'redpagos': {
        'title': 'RedPagos',
        'lines': [
            'Al seleccionar este método, te enviamos por WhatsApp los datos para hacer el giro.',
        ],
    },
}

# Create your views here.
def inicio(request):
    products = list(Producto.objects.all())
    joyas = list(Joya.objects.all())

    return render(request, 'index.html', {
        'products': products,
        'joyas': joyas,
    })


def catalogo_joyas(request):
    joyas = Joya.objects.all()
    return render(request, 'muestrario.html', {'joyas': joyas})


def agregar_al_carrito(request, tipo, producto_id):
    if not request.user.is_authenticated:
        next_url = request.GET.get('next') or request.get_full_path()
        login_url = f"{reverse('login')}?next={quote(next_url)}"
        return redirect(login_url)

    cart = Cart(request)
    if tipo == 'joya':
        producto = get_object_or_404(Joya, id=producto_id)
    else:
        producto = get_object_or_404(Producto, id=producto_id)
    cart.add(product=producto, tipo=tipo)
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('inicio')
    return redirect(next_url)


def eliminar_del_carrito(request, tipo, producto_id):
    cart = Cart(request)
    if tipo == 'joya':
        producto = get_object_or_404(Joya, id=producto_id)
    else:
        producto = get_object_or_404(Producto, id=producto_id)
    cart.remove(producto)
    return redirect('carrito')


def carrito_detalle(request):
    cart_items = request.session.get('cart', {})
    total_carrito = sum(
        float(item['precio']) * item['cantidad']
        for item in cart_items.values()
    )
    return render(request, 'carrito.html', {
        'cart_items': cart_items,
        'total_carrito': total_carrito,
        'checkout_modal_open': False,
    })


def finalizar_compra(request):
    if not request.user.is_authenticated:
        login_url = f"{reverse('login')}?next={quote(reverse('carrito'))}"
        return redirect(login_url)

    if request.method != 'POST':
        return redirect('carrito')

    cart_items = request.session.get('cart', {})
    if not cart_items:
        return render(request, 'carrito.html', {
            'cart_items': {},
            'total_carrito': 0,
            'checkout_modal_open': True,
            'checkout_error': 'Su carrito está vacío.',
            'checkout_unidades': 0,
        })

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    customer_name = profile.full_name or request.user.get_full_name() or request.user.username
    domicilio = profile.address or 'No informado'
    ciudad = profile.department or 'No informada'
    estado = profile.department or 'No informado'

    checkout_items = {key: value.copy() for key, value in cart_items.items()}
    checkout_unidades = sum(item.get('cantidad', 0) for item in checkout_items.values())

    total_carrito = Decimal('0.00')
    productos_detalle = []
    items_orden = []
    for item in checkout_items.values():
        cantidad = int(item.get('cantidad', 1))
        precio = Decimal(str(item.get('precio', '0')))
        subtotal = precio * cantidad
        total_carrito += subtotal
        productos_detalle.append(f"{item.get('nombre', 'Producto')} x{cantidad} - ${subtotal}")
        items_orden.append({
            'nombre_producto': item.get('nombre', 'Producto'),
            'tipo_producto': item.get('tipo', 'producto'),
            'cantidad': cantidad,
            'precio_unitario': precio,
            'subtotal': subtotal,
            'product_id': item.get('product_id'),
        })

    with transaction.atomic():
        compra = OrdenCompra.objects.create(
            user=request.user,
            nombre=customer_name[:30],
            domicilio=domicilio[:50],
            ciudad=ciudad[:60],
            estado=estado[:50],
            pais='Uruguay',
            total=total_carrito,
        )

        for item_data in items_orden:
            item_payload = {
                'orden': compra,
                'nombre_producto': item_data['nombre_producto'][:120],
                'tipo_producto': item_data['tipo_producto'],
                'cantidad': item_data['cantidad'],
                'precio_unitario': item_data['precio_unitario'],
                'subtotal': item_data['subtotal'],
            }
            if item_data['tipo_producto'] == 'joya':
                item_payload['joya_id'] = item_data['product_id']
            else:
                item_payload['producto_id'] = item_data['product_id']
            OrdenCompraItem.objects.create(**item_payload)

        Adquirido.objects.create(
            user=request.user,
            numero_orden=compra.numero_orden,
            nombre=customer_name[:30],
            domicilio=domicilio[:50],
            ciudad=ciudad[:60],
            estado=estado[:50],
            pais='Uruguay',
            sitioweb='https://ditaboutique.local/orden',
            productos='\n'.join(productos_detalle),
            total=total_carrito,
        )

        for item in checkout_items.values():
            tipo = item.get('tipo', 'producto')
            cantidad_comprada = item.get('cantidad', 1)
            product_id = item.get('product_id')
            if tipo == 'joya':
                continue
            try:
                producto = Producto.objects.get(id=product_id)
                producto.cantidad = max(0, producto.cantidad - cantidad_comprada)
                producto.save()
            except Producto.DoesNotExist:
                pass

        cart = Cart(request)
        cart.clear()

    return redirect(reverse('checkout_orden', args=[compra.numero_orden]))


def checkout_orden(request, numero_orden):
    if not request.user.is_authenticated:
        login_url = f"{reverse('login')}?next={request.get_full_path()}"
        return redirect(login_url)
    compra = get_object_or_404(OrdenCompra.objects.prefetch_related('items'), numero_orden=numero_orden, user=request.user)
    return render(request, 'finalizar_compra.html', {'compra': compra})


def actualizar_metodo_pago(request, numero_orden):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Autenticacion requerida.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Metodo no permitido.'}, status=405)

    compra = get_object_or_404(OrdenCompra, numero_orden=numero_orden, user=request.user)
    method = request.POST.get('method', '').strip()
    valid_methods = {'transferencia', 'efectivo', 'giros', 'deposito'}
    if method not in valid_methods:
        return JsonResponse({'ok': False, 'error': 'Metodo de pago invalido.'}, status=400)

    compra.metodo_pago = method
    compra.save(update_fields=['metodo_pago'])
    return JsonResponse({
        'ok': True,
        'metodo_pago': compra.metodo_pago,
        'metodo_pago_label': compra.get_metodo_pago_display(),
        'estado_orden': compra.estado_orden,
        'estado_orden_label': compra.get_estado_orden_display(),
        'estado_orden_css': compra.estado_badge_class,
    })


def payment_method_detail(request, method):
    method_data = PAYMENT_METHODS.get(method)
    if not method_data:
        raise Http404('Método de pago no encontrado.')

    next_url = request.GET.get('next') or reverse('carrito')
    return render(request, 'payment_method_detail.html', {
        'method_title': method_data['title'],
        'method_lines': method_data['lines'],
        'next_url': next_url,
    })


def tienda(request, categoria=None):
    products = Producto.objects.all()
    selected_category = categoria or request.GET.get('categoria')
    if selected_category:
        products = products.filter(categoria=selected_category)

    category_choices = [
        ('bijou', 'Bijou'),
        ('acero_quirurgico', 'Acero quirúrgico'),
        ('enchapados', 'Enchapados'),
        ('accesorios', 'Accesorios'),
        ('alpaca', 'Alpaca'),
        ('gangas', 'Gangas'),
        ('temporada_invierno', 'Temporada de invierno'),
    ]

    return render(request, 'tienda.html', {
        'products': products,
        'selected_category': selected_category,
        'category_choices': category_choices,
    })


def buscar(request):
    query = request.GET.get('q', '').strip()
    products = []
    if query:
        products = Producto.objects.filter(
            Q(nombre__icontains=query)
        )
    context = {
        'query': query,
        'products': products,
    }
    return render(request, 'buscar.html', context)


def ingresar(request):
    if request.user.is_authenticated:
        next_url = request.GET.get('next') or reverse('inicio')
        return redirect(next_url)

    next_url = request.POST.get('next') or request.GET.get('next') or reverse('inicio')
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect(next_url)

    return render(request, 'ingresar.html', {
        'formulario': form,
        'next': next_url,
    })


def registro(request):
    if request.user.is_authenticated:
        return redirect('mi_cuenta')

    next_url = request.POST.get('next') or request.GET.get('next') or reverse('inicio')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'¡Cuenta creada para {username}! Ya puedes iniciar sesión.')
            return redirect(f"{reverse('login')}?next={quote(next_url)}")
    else:
        form = UserCreationForm()

    return render(request, 'registro.html', {
        'formulario': form,
        'next': next_url,
    })

def mi_cuenta(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('ingresar')}?next={reverse('mi_cuenta')}")

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    is_edit_mode = request.GET.get('edit') == '1'
    has_saved_data = bool(
        profile.full_name or profile.phone or profile.address or profile.department or request.user.email
    )

    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name', '').strip()
        profile.phone = request.POST.get('phone', '').strip()
        profile.address = request.POST.get('address', '').strip()
        profile.department = request.POST.get('department', '').strip()
        email = request.POST.get('email', '').strip()

        if email:
            request.user.email = email
            request.user.save()

        profile.save()
        messages.success(request, 'Tus datos personales se guardaron correctamente.')
        return redirect(reverse('mi_cuenta'))

    return render(request, 'mi_cuenta.html', {
        'page_title': 'Mi Cuenta',
        'profile': profile,
        'is_edit_mode': is_edit_mode,
        'has_saved_data': has_saved_data,
        'ordenes_recientes': OrdenCompra.objects.filter(user=request.user).prefetch_related('items')[:3],
        'user': request.user,
    })


def mis_compras(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('ingresar')}?next={reverse('mis_compras')}")

    compras = OrdenCompra.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'mis_compras.html', {
        'page_title': 'Mis Compras',
        'compras': compras,
    })


def cerrar_sesion(request):
    logout(request)
    return redirect('inicio')


def suscribirse(request):
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', reverse('inicio')))

    nombre = request.POST.get('nombre', '').strip()
    email = request.POST.get('email', '').strip()
    next_url = request.META.get('HTTP_REFERER', reverse('inicio'))

    if not email:
        messages.error(request, 'Por favor ingresá tu correo para suscribirte.')
        return redirect(next_url)

    subscriber, created = Subscriber.objects.get_or_create(email=email)
    if created:
        subscriber.nombre = nombre
        subscriber.save()
        messages.success(request, 'Gracias por suscribirte. Ya sos usuario suscripto.')
    else:
        messages.info(request, 'Este correo ya está registrado como suscripto.')

    return redirect(next_url)


def placeholder(request, page=''):
    page_slug = page.replace('-', '_').rstrip('/') or 'página'
    template_name = f"{page_slug}.html"
    context = {
        'page_title': page_slug.replace('_', ' ').title(),
        'page_name': page_slug.replace('_', ' ').title(),
    }
    try:
        return render(request, template_name, context)
    except TemplateDoesNotExist:
        context['message'] = 'Esta página aún no está construida. Pronto estará disponible.'
        return render(request, 'placeholder.html', context)

class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["hero"] = {
            "image_url": "/media/banners/hero.jpg",
            "eyebrow":   "Nueva Colección",
            "title":     "Bags Weekend",
            "subtitle":  "Diseño y calidad en cada detalle.",
            "cta_text":  "Ver colección",
            "cta_url":   "/carteras/",
            "overlay":   "left",   # "left" | "center" | "right"
        }

        # Reemplazar con querysets reales:
        # from .models import Product
        # ctx["featured_products"] = Product.objects.filter(is_featured=True)[:16]
        ctx["featured_products"] = []
        ctx["sale_products"]     = []

        ctx["cat_banners_top"] = [
            {"image_url": "/media/banners/plata.jpg",
             "label": "Plata", "url": "/plata/"},
            {"image_url": "/media/banners/acero.jpg",
             "label": "Acero", "url": "/acero/"},
        ]
        ctx["cat_banners_mid"] = [
            {"image_url": "/media/banners/carteras.jpg",
             "label": "Carteras", "url": "/carteras/"},
            {"image_url": "/media/banners/pashminas.jpg",
             "label": "Pashminas", "url": "/accesorios/pashminas/"},
            {"image_url": "/media/banners/bijou.jpg",
             "label": "Bijou", "url": "/bijou/"},
        ]
        ctx["promo"] = {
            "eyebrow":  "Oferta especial",
            "title":    "15% OFF con Scotiabank",
            "subtitle": "En todos los productos",
            "logo_url": "/static/img/scotiabank.svg",
            "cta_url":  "/catalogo/",
            "cta_text": "Ver ofertas",
            "bg_color": "#1a1a1a",
        }
        return ctx
    
def global_context(request):
    return {
        "site_name":  "DitaBoutique",
        "cart_count": request.session.get("cart_count", 0),
        "total_carrito": sum(
            float(item['precio']) * item['cantidad']
            for item in request.session.get('cart', {}).values()
        ),
        "unidades_carrito": sum(
            item['cantidad']
            for item in request.session.get('cart', {}).values()
        ),

        "banner_text": "Envios gratis a partir de $1500 a todo el pais",
        "banner_link": "",
        "banner_cta":  "",

        "nav_categories": [
            {
                "name": "Bijou", "url": "/bijou/",
                "is_sale": False,
                "subcategories": [
                    {"name": "Anillos",   "url": "/bijou/anillos/"},
                    {"name": "Collares",  "url": "/bijou/collares/"},
                    {"name": "Caravanas", "url": "/bijou/caravanas/"},
                    {"name": "Pulseras",  "url": "/bijou/pulseras/"},
                ],
            },
            {
                "name": "Acero quirúrgico", "url": "/acero-quirurgico/", "is_sale": False,
                "subcategories": [],
            },
            {
                "name": "Enchapados", "url": "/plata/", "is_sale": False,
                "subcategories": [
                    {"name": "Anillos",         "url": "/plata/anillos/"},
                    {"name": "Collares",         "url": "/plata/collares/"},
                    {"name": "Cadenas y dijes",  "url": "/plata/cadenas-y-dijes/"},
                ],
            },
            {
                "name": "Alpaca", "url": "/alpaca/", "is_sale": False,
                "subcategories": [],
            },
            {
                "name": "Gangas", "url": "/catalogo/outlet/",
                "is_sale": True, "subcategories": [],
            },
            {
                "name": "Accesorios", "url": "/accesorios/",
                "is_sale": False, "subcategories": [],
            },
            {
                "name": "Temporada de invierno", "url": "/temporada-invierno/",
                "is_sale": False,
                "is_winter": True,
                "subcategories": [],
            },
        ],

        "social_links": {
            "facebook":  "https://www.facebook.com/share/1KCGT9QAFv/",
            "instagram": "https://www.instagram.com/ditaboutiique?igsh=MW14Z3NkZGk1YWp3dA==",
        },
        "payment_methods": [],
        "footer_links": {
            "empresa":   [
                {"label": "Empresa",  "url": reverse('page', kwargs={'page': 'empresa'})},
                {"label": "Tienda",   "url": reverse('tienda')},
                {"label": "Contacto", "url": reverse('page', kwargs={'page': 'contacto'})},
            ],
            "comprar":   [
                {"label": "Cómo comprar",       "url": reverse('page', kwargs={'page': 'como-comprar'})},
                {"label": "Política de cambios","url": reverse('page', kwargs={'page': 'politica-de-cambios'})},
                {"label": "Envíos",             "url": reverse('page', kwargs={'page': 'envios'})},
                {"label": "Términos",           "url": reverse('page', kwargs={'page': 'terminos'})},
            ],
            "mi_cuenta": [
                {"label": "Mi compra",   "url": reverse('mi_cuenta')},
                {"label": "Mis compras", "url": reverse('mis_compras')},
            ],
        },
        "footer_address": "Tu calle 1234, Montevideo",
        "footer_phone":   "2400 0000",
        "footer_email":   "info@mitienda.com.uy",
        "footer_hours":   "Lunes a Viernes 9 a 18 hs",
    }