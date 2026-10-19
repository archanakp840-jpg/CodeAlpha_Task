rname': 'staffer', 'password': 'SafePass!4931',
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
