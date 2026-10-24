from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from .models import Category, Product, Cart, CartItem, Order, OrderItem, NewsletterSubscriber


class StorefrontRoleTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Home', slug='home')
        self.product = Product.objects.create(
            category=category, name='Linen Throw', slug='linen-throw',
            description='A soft throw for the sofa.', price='1299.00', stock=5,
            is_active=True,
        )

    def test_customer_registration_is_available_and_signs_customer_in(self):
        response = self.client.post(reverse('register'), {
            'username': 'shopper', 'password1': 'SafePass!4931',
            'password2': 'SafePass!4931',
        })
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(User.objects.get(username='shopper').is_active)
        self.assertEqual(str(User.objects.get(username='shopper').pk), self.client.session.get('_auth_user_id'))

    def test_customer_sees_add_to_cart_and_can_add_product(self):
        User.objects.create_user(username='shopper', password='SafePass!4931')
        self.client.login(username='shopper', password='SafePass!4931')
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Add to cart')
        self.client.post(reverse('add_to_cart', args=[self.product.id]))
        from .models import CartItem
        self.assertEqual(CartItem.objects.filter(cart__user__username='shopper', product=self.product).get().quantity, 1)

    def test_staff_gets_product_edit_link_and_no_cart_action(self):
        staff = User.objects.create_user(username='staffer', password='SafePass!4931', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='change_product', content_type__app_label='store'))
        self.client.login(username='staffer', password='SafePass!4931')
        response = self.client.get(reverse('home'))
        self.assertContains(response, reverse('admin:store_product_change', args=[self.product.id]))
        self.assertContains(response, 'Product details')
        self.assertNotContains(response, 'Add to bag')

    def test_admin_can_review_accounts_and_admin_activity(self):
        admin_user = User.objects.create_superuser(username='admin', email='admin@example.com', password='SafePass!4931')
        self.client.force_login(admin_user)
        self.assertEqual(self.client.get(reverse('admin:auth_user_changelist')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:admin_logentry_changelist')).status_code, 200)


    def test_customer_and_staff_login_are_separate(self):
        User.objects.create_user(username='customer', password='SafePass!4931')
        User.objects.create_user(username='staffer', password='SafePass!4931', is_staff=True)

        response = self.client.post(reverse('login'), {
            'username': 'staffer', 'password': 'SafePass!4931',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff and admin accounts should use staff sign-in.')

        response = self.client.post(reverse('staff_login'), {
            'username': 'customer', 'password': 'SafePass!4931',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This sign-in is for staff and admin accounts.')

        response = self.client.post(reverse('staff_login'), {
            'username': 'staffer', 'password': 'SafePass!4931',
        })
        self.assertRedirects(response, reverse('admin:index'), fetch_redirect_response=False)

    def test_logout_returns_to_storefront(self):
        customer = User.objects.create_user(username='customer', password='SafePass!4931')
        self.client.force_login(customer)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_checkout_snapshots_product_and_duplicate_submit_is_idempotent(self):
        customer = User.objects.create_user(username='buyer', password='SafePass!4931')
        self.client.force_login(customer)
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.client.get(reverse('checkout'))
        key = self.client.session['checkout_key']
        payload = {
            'full_name': 'Buyer Example', 'phone': '9876543210',
            'email': 'buyer@example.com', 'address': '12 Market Road',
            'city': 'Pune', 'state': 'Maharashtra', 'pin_code': '411001',
            'payment_method': 'demo', 'checkout_key': key,
        }
        response = self.client.post(reverse('checkout'), payload)
        order = Order.objects.get(user=customer)
        line = OrderItem.objects.get(order=order)
        self.assertRedirects(response, reverse('order_success', args=[order.id]), fetch_redirect_response=False)
        self.assertEqual(order.total_amount, 2598)
        self.assertEqual(order.status, 'pending')
        self.assertTrue(order.order_number.startswith('SM-'))
        self.assertEqual(line.product_name, 'Linen Throw')
        self.assertEqual(line.price, 1299)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        duplicate = self.client.post(reverse('checkout'), payload)
        self.assertRedirects(duplicate, reverse('order_success', args=[order.id]), fetch_redirect_response=False)
        self.assertEqual(Order.objects.filter(user=customer).count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_checkout_rejects_invalid_pin_without_order_or_stock_change(self):
        customer = User.objects.create_user(username='buyer2', password='SafePass!4931')
        self.client.force_login(customer)
        cart = Cart.objects.create(user=customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.get(reverse('checkout'))
        response = self.client.post(reverse('checkout'), {
            'full_name': 'Buyer Example', 'phone': '9876543210',
            'email': 'buyer@example.com', 'address': '12 Market Road',
            'city': 'Pune', 'state': 'Maharashtra', 'pin_code': 'bad',
            'payment_method': 'cod', 'checkout_key': self.client.session['checkout_key'],
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a valid 6-digit PIN code.')
        self.assertFalse(Order.objects.filter(user=customer).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_product_listing_search_filters_and_sorts_from_database(self):
        second = Product.objects.create(
            category=self.product.category, name='Cotton Cushion', slug='cotton-cushion',
            description='Soft cotton cushion cover.', price='499.00', stock=0, is_new=True,
        )
        response = self.client.get(reverse('product_list'), {'q': 'cushion', 'available': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No products match those filters.')
        response = self.client.get(reverse('product_list'), {'category': 'home', 'sort': 'price_asc'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Linen Throw')
        self.assertContains(response, 'Cotton Cushion')
        self.assertEqual(response.context['products'][0], second)

    def test_newsletter_subscription_is_saved_and_duplicate_is_safe(self):
        response = self.client.post(reverse('newsletter_subscribe'), {'email': 'Reader@Example.com'})
        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)
        self.assertEqual(NewsletterSubscriber.objects.get().email, 'reader@example.com')
        self.client.post(reverse('newsletter_subscribe'), {'email': 'reader@example.com'})
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)
