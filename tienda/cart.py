class Cart:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, tipo='producto'):
        product_id = str(product.id)
        image_url = ''
        if hasattr(product, 'imagen') and product.imagen:
            image_url = product.imagen.url
        elif hasattr(product, 'portada') and product.portada:
            image_url = product.portada.url

        if product_id not in self.cart:
            self.cart[product_id] = {
                'product_id': product.id,
                'tipo': tipo,
                'nombre': product.nombre,
                'precio': str(product.precio),
                'cantidad': 1,
                'imagen': image_url,
            }
        else:
            self.cart[product_id]['cantidad'] += 1
        self.save()

    def save(self):
        self.session['cart'] = self.cart
        self.session['cart_count'] = sum(item['cantidad'] for item in self.cart.values())
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        self.session['cart'] = {}
        self.session['cart_count'] = 0
        self.save()
