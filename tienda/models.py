from django.contrib.auth.models import User
from django.db import DatabaseError, models
from django.utils import timezone

# Create your models here.

class Adquirido(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='adquiridos')
    nombre = models.CharField(max_length=30)
    domicilio = models.CharField(max_length=50)
    ciudad = models.CharField(max_length=60)
    estado = models.CharField(max_length=50)
    pais = models.CharField(max_length=50)
    sitioweb = models.URLField()
    productos = models.TextField(blank=True, default='')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nombre} - {self.created_at:%Y-%m-%d}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


class Subscriber(models.Model):
    nombre = models.CharField(max_length=120, blank=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.email


CATEGORY_CHOICES = [
    ('bijou', 'Bijou'),
    ('acero_quirurgico', 'Acero quirúrgico'),
    ('enchapados', 'Enchapados'),
    ('alpaca', 'Alpaca'),
    ('gangas', 'Gangas'),
]


class Joya(models.Model):
    nombre = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='joyas/')
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='bijou',
    )
    descripcion = models.TextField(blank=True, default='')

    def gallery_urls(self):
        urls = []
        if self.imagen:
            urls.append(self.imagen.url)
        try:
            urls.extend([img.imagen.url for img in self.imagenes.all() if img.imagen])
        except DatabaseError:
            # If the related image table has not been migrated yet,
            # return the base image URL only and avoid crashing the page.
            pass
        return urls

    def __str__(self):
        return self.nombre

class JoyaImagen(models.Model):
    joya = models.ForeignKey(Joya, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='joyas/')
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"Imagen de {self.joya.nombre} ({self.orden})"


class Producto(models.Model):
    nombre = models.CharField(max_length=30)
    precio = models.DecimalField(decimal_places=2, default=0.0, max_digits=10)
    portada = models.ImageField(upload_to='productos/')
    cantidad = models.IntegerField(default=0)
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='enchapados',
    )
    temporada_invierno = models.BooleanField(default=False)
    descripcion = models.TextField(blank=True, default='')

    def gallery_urls(self):
        urls = []
        if self.portada:
            urls.append(self.portada.url)
        try:
            urls.extend([img.imagen.url for img in self.imagenes.all() if img.imagen])
        except DatabaseError:
            # If the related image table has not been migrated yet,
            # return the main portada URL and avoid crashing the page.
            pass
        return urls

    def __str__(self):
        return self.nombre


class ProductoImagen(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='productos/')
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"Imagen de {self.producto.nombre} ({self.orden})"