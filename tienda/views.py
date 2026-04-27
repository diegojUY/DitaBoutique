from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template import TemplateDoesNotExist
from django.urls import reverse
from django.views.generic import TemplateView
from urllib.parse import quote

from .cart import Cart
from .models import Adquirido, Producto, Joya, Subscriber, UserProfile

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
    })


def finalizar_compra(request):
    cart_items = request.session.get('cart', {})
    cart_empty = not bool(cart_items)

    if not cart_empty:
        for key, item in cart_items.items():
            tipo = item.get('tipo', 'producto')
            cantidad_comprada = item.get('cantidad', 1)
            product_id = item.get('product_id')
            if tipo == 'joya':
                try:
                    joya = Joya.objects.get(id=product_id)
                    joya.precio  # Joyas don't have cantidad field by default
                except Joya.DoesNotExist:
                    pass
            else:
                try:
                    producto = Producto.objects.get(id=product_id)
                    producto.cantidad = max(0, producto.cantidad - cantidad_comprada)
                    producto.save()
                except Producto.DoesNotExist:
                    pass

        cart = Cart(request)
        cart.clear()

    return render(request, 'finalizar_compra.html', {
        'cart_empty': cart_empty,
    })


def tienda(request, categoria=None):
    products = Producto.objects.all()
    selected_category = categoria or request.GET.get('categoria')
    if selected_category:
        if selected_category == 'accesorios':
            products = products.exclude(categoria='gangas')
        elif selected_category == 'temporada_invierno':
            products = products.filter(temporada_invierno=True)
        else:
            products = products.filter(categoria=selected_category)

    category_choices = [
        ('bijou', 'Bijou'),
        ('acero_quirurgico', 'Acero quirúrgico'),
        ('enchapados', 'Enchapados'),
        ('alpaca', 'Alpaca'),
        ('gangas', 'Gangas'),
        ('accesorios', 'Accesorios'),
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
        'user': request.user,
    })


def mis_compras(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('ingresar')}?next={reverse('mis_compras')}")

    compras = Adquirido.objects.filter(user=request.user).order_by('-created_at')
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