from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.core.paginator import Paginator
from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from uuid import uuid4
from .forms import CheckoutForm, NewsletterForm
from .models import Product, Category, Cart, CartItem, Order, OrderItem, NewsletterSubscriber


def home(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query))
    if category_slug:
        products = products.filter(category__slug=category_slug)
    categories = Category.objects.all()[:5]
    featured = Product.objects.filter(is_active=True, is_featured=True).select_related('category')[:4]
    if not featured:
        featured = products.order_by('-created_at')[:4]
    return render(request, 'store/home.html', {
        'products': products, 'categories': categories, 'query': query,
        'selected_category': category_slug,
        'featured_products': featured,
        'new_products': Product.objects.filter(is_active=True, is_new=True).select_related('category').order_by('-created_at')[:4],
        'offer_products': Product.objects.filter(is_active=True, old_price__gt=F('price')).select_related('category')[:3],
    })


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    price_min = request.GET.get('min_price', '').strip()
    price_max = request.GET.get('max_price', '').strip()
    sort = request.GET.get('sort', 'featured')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query))
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if request.GET.get('available') == '1':
        products = products.filter(stock__gt=0)
    if request.GET.get('new') == '1':
        products = products.filter(is_new=True)
    for value, lookup in ((price_min, 'price__gte'), (price_max, 'price__lte')):
        if value:
            try:
                products = products.filter(**{lookup: Decimal(value)})
            except InvalidOperation:
                pass
    ordering = {'price_asc': 'price', 'price_desc': '-price', 'newest': '-created_at'}.get(sort, '-is_featured')
    pagessages.success(request, f'{product.name} added to your cart.')
    else:
        item.delete()
        messages.error(request, f'{product.name} is out of stock.')
    return redirect('cart')


@login_required
def cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product')
    return render(request, 'store/cart.html', {'cart_items': items, 'total': sum(i.total_price for i in items)})


@login_required
def update_cart(request, item_id, action):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        if action == 'increase' and item.quantity < item.product.stock:
            item.quantity += 1
            item.save(update_fields=['quantity'])
        elif action == 'decrease' and item.quantity > 1:
            item.quantity -= 1
            item.save(update_fields=['quantity'])
    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        get_object_or_404(CartItem, id=item_id, cart__user=request.user).delete()
    return redirect('cart')


@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = list(cart.items.select_related('product').filter(product__is_active=True))
    checkout_key = request.session.get('checkout_key')
    if not checkout_key:
        checkout_key = str(uuid4())
        request.session['checkout_key'] = checkout_key
    if request.method == 'POST':
        submitted_key = request.POST.get('checkout_key')
        existing = Order.objects.filter(user=request.user, checkout_key=submitted_key).first()
        if existing:
            return redirect('order_success', order_id=existing.id)
    if not items:
        messages.info(request, 'Your cart is empty.')
        return redirect('cart')
    total = sum(item.total_price for item in items)
    form = CheckoutForm(request.POST or None, initial={
        'email': request.user.email,
        'full_name': request.user.get_full_name(),
        'checkout_key': checkout_key,
    })
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            with transaction.atomic():
                # Re-read cart and current catalog prices in the transaction. Stock is
                # decremented conditionally, which is safe on SQLite as well as PostgreSQL.
                current_items = list(cart.items.select_related('product').filter(product__is_active=True))
                if not current_items:
                    messages.error(request, 'Your cart is empty or contains unavailable products.')
                    return redirect('cart')
                fresh_total = sum(item.product.price * item.quantity for item in current_items)
                order = Order.objects.create(
                    user=request.user,
                    order_number=f'SM-{uuid4().hex[:12].upper()}',
                    checkoutNFO_PAGES.get(slug)
    if not page:
        return render(request, 'store/information.html', status=404, context={'title': 'Page not found', 'body': 'This information page is not available.'})
    return render(request, 'store/information.html', {'title': page[0], 'body': page[1]})


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:4]
    return render(request, 'store/product_detail.html', {'product': product, 'related_products': related})


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        auth_login(request, user)
        messages.success(request, 'Your customer account is ready. Welcome to HomeMate!')
        return redirect('home')
    return render(request, 'registration/register.html', {'form': form})


def account_login(request, staff_login=False):
    if request.user.is_authenticated:
        return redirect('admin:index' if request.user.is_staff else 'home')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if staff_login and not user.is_staff:
            form.add_error(None, 'This sign-in is for staff and admin accounts. Use customer sign-in instead.')
        elif not staff_login and user.is_staff:
            form.add_error(None, 'Staff and admin accounts should use staff sign-in.')
        else:
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}.')
            next_url = request.POST.get('next') or request.GET.get('next', '')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
            return redirect('admin:index' if staff_login else 'home')
    return render(request, 'registration/login.html', {'form': form, 'staff_login': staff_login})


def customer_login(request):
    return account_login(request, staff_login=False)


def staff_login(request):
    return account_login(request, staff_login=True)


@login_required
def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('home')
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    requested = int(request.POST.get('quantity', 1))
    requested = max(1, min(requested, product.stock))
    item.quantity = min(product.stock, requested if created else item.quantity + requested)
    if item.quantity:
        item.save()
        minator = Paginator(products.order_by(ordering, '-created_at'), 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    pagination_params = request.GET.copy()
    pagination_params.pop('page', None)
    return render(request, 'store/product_list.html', {
        'products': page_obj.object_list, 'page_obj': page_obj, 'categories': Category.objects.all(),
        'query': query, 'selected_category': category_slug, 'sort': sort,
        'price_min': price_min, 'price_max': price_max,
        'available': request.GET.get('available') == '1', 'new_only': request.GET.get('new') == '1',
        'result_count': paginator.count,
        'pagination_query': pagination_params.urlencode(),
    })


def newsletter_subscribe(request):
    if request.method != 'POST':
        return redirect('home')
    form = NewsletterForm(request.POST)
    if form.is_valid():
        _, created = NewsletterSubscriber.objects.get_or_create(email=form.cleaned_data['email'].lower())
        messages.success(request, 'Thanks for subscribing!' if created else 'You are already on the list.')
    else:
        messages.error(request, 'Enter a valid email address to subscribe.')
    referrer = request.META.get('HTTP_REFERER', '')
    if url_has_allowed_host_and_scheme(referrer, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(referrer)
    return redirect('home')


INFO_PAGES = {
    'shipping': ('Delivery information', 'This HomeMate build is a local demonstration. Orders are recorded in the development database and shipment progress can be simulated by staff in the admin area. No real courier service is connected.'),
    'returns': ('Returns & refunds', 'This is an educational demonstration storefront and does not fulfill real purchases. The mock payment option never collects payment details or charges money.'),
    'privacy': ('Privacy', 'This local demo stores the account, delivery, order, and newsletter information needed to demonstrate store features. Django hashes account passwords. No payment card information is collected. For a public launch, replace this notice with the store operator’s reviewed privacy policy.'),
    'terms': ('Terms & conditions', 'HomeMate is a demonstration store for browsing and testing order flows. Orders and mock payments do not represent real purchases. A real store would need operator contact details, fulfillment terms, and payment-provider integration.'),
    'faq': ('Frequently asked questions', 'Is payment real? No. Cash on Delivery is a demo selection and mock payment does not take payment. Where is my order? Sign in and open My orders to view the recorded order status. Can products be managed? Authorized staff can use the Django admin.'),
    'contact': ('Contact HomeMate', 'This demonstration does not have a staffed customer support address. The checkout and order-history pages are available for trying the local shopping flow.'),
}


def information_page(request, slug):
    page = I_key=data['checkout_key'],
                    full_name=data['full_name'], phone=data['phone'], email=data['email'],
                    address=data['address'], city=data['city'], state=data['state'],
                    pin_code=data['pin_code'], payment_method=data['payment_method'],
                    status='pending', total_amount=fresh_total,
                )
                for item in current_items:
                    product = item.product
                    changed = Product.objects.filter(
                        pk=product.pk, is_active=True, stock__gte=item.quantity
                    ).update(stock=F('stock') - item.quantity)
                    if not changed:
                        raise ValueError(f'{product.name} no longer has enough stock. Please review your cart.')
                    OrderItem.objects.create(
                        order=order, product=product, product_name=product.name,
                        quantity=item.quantity, price=product.price,
                    )
                cart.items.all().delete()
        except ValueError as error:
            messages.error(request, str(error))
            return redirect('cart')
        except IntegrityError:
            # A simultaneous repeat submit can race the earlier idempotency lookup.
            existing = Order.objects.filter(user=request.user, checkout_key=data['checkout_key']).first()
            if existing:
                return redirect('order_success', order_id=existing.id)
            raise
        request.session.pop('checkout_key', None)
        return redirect('order_success', order_id=order.id)
    return render(request, 'store/checkout.html', {
        'cart_items': items, 'total': total, 'form': form,
    })


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), id=order_id, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})


@login_required
def order_history(request):
    orders = request.user.orders.prefetch_related('items__product').order_by('-created_at')
    return render(request, 'store/orders.html', {'orders': orders})
