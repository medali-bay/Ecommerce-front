from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Category, Product, Order, StockMovement, OrderItem


class OrderStockTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.category = Category.objects.create(
            name="Electronics"
        )

        self.product = Product.objects.create(
            category=self.category,
            name="Mouse",
            description="Wireless mouse",
            price="25.00",
            stock=10
        )

    def test_create_order_decreases_product_stock(self):
        response = self.client.post(
            "/api/orders/",
            {
                "customer_name": "Test Customer",
                "city": "Berlin",
                "phone_number": "0123456789",
                "notes": "Testing stock decrease.",
                "order_items": [
                    {
                        "product": self.product.id,
                        "quantity": 2
                    }
                ]
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        order = Order.objects.first()
        self.assertEqual(order.total_price, self.product.price * 2)

        stock_movement = StockMovement.objects.first()
        self.assertEqual(stock_movement.quantity_change, -2)
        self.assertEqual(stock_movement.reason, "order_created")

    def test_cancel_order_restores_product_stock(self):
        response = self.client.post(
            "/api/orders/",
            {
                "customer_name": "Test Customer",
                "city": "Berlin",
                "phone_number": "0123456789",
                "notes": "Testing stock restoration.",
                "order_items": [
                    {
                        "product": self.product.id,
                        "quantity": 2
                    }
                ]
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)

        order_id = response.data["id"]

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        admin_user = User.objects.create_superuser(
            username="admin",
            password="admin12345"
        )

        self.client.force_authenticate(user=admin_user)

        cancel_response = self.client.post(
            f"/api/orders/{order_id}/cancel_order/",
            {},
            format="json"
        )

        self.assertEqual(cancel_response.status_code, 200)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, "cancelled")

    def test_admin_can_validate_order_and_history_is_created(self):
     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Testing validation.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)

     order_id = response.data["id"]

     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     validate_response = self.client.post(
        f"/api/orders/{order_id}/validate_order/",
        {},
        format="json"
    )

     self.assertEqual(validate_response.status_code, 200)

     order = Order.objects.get(id=order_id)
     self.assertEqual(order.status, "validated")

     history = order.status_history.first()
     self.assertIsNotNone(history)
     self.assertEqual(history.old_status, "pending")
     self.assertEqual(history.new_status, "validated")
     self.assertEqual(history.changed_by.username, "admin") 

    def test_non_admin_cannot_validate_order(self):
     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Testing non-admin validation block.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)

     order_id = response.data["id"]

     normal_user = User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     self.client.force_authenticate(user=normal_user)

     validate_response = self.client.post(
        f"/api/orders/{order_id}/validate_order/",
        {},
        format="json"
    )

     self.assertEqual(validate_response.status_code, 403)

     order = Order.objects.get(id=order_id)
     self.assertEqual(order.status, "pending")   

    def test_pending_order_cannot_be_delivered(self):
     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Testing delivery restriction.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)

     order_id = response.data["id"]

     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     deliver_response = self.client.post(
        f"/api/orders/{order_id}/deliver_order/",
        {},
        format="json"
    )

     self.assertEqual(deliver_response.status_code, 400)

     order = Order.objects.get(id=order_id)
     self.assertEqual(order.status, "pending") 


    def test_validated_order_can_be_delivered(self):
     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Testing successful delivery.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)

     order_id = response.data["id"]

     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     validate_response = self.client.post(
        f"/api/orders/{order_id}/validate_order/",
        {},
        format="json"
    )

     self.assertEqual(validate_response.status_code, 200)

     deliver_response = self.client.post(
        f"/api/orders/{order_id}/deliver_order/",
        {},
        format="json"
    )

     self.assertEqual(deliver_response.status_code, 200)

     order = Order.objects.get(id=order_id)
     self.assertEqual(order.status, "delivered")

     history_records = order.status_history.all()

     self.assertEqual(history_records.count(), 2)

     self.assertEqual(history_records[0].old_status, "pending")
     self.assertEqual(history_records[0].new_status, "validated")

     self.assertEqual(history_records[1].old_status, "validated")
     self.assertEqual(history_records[1].new_status, "delivered") 


    def test_guest_can_create_order_but_cannot_list_orders(self):
     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Guest Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Guest order test.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)

     list_response = self.client.get("/api/orders/")

     self.assertEqual(list_response.status_code, 200)
    

    def test_customer_can_only_see_own_orders(self):
     user1 = User.objects.create_user(
        username="customer1",
        password="customer12345"
    )

     user2 = User.objects.create_user(
        username="customer2",
        password="customer12345"
    )

    # Create order for customer1
     Order.objects.create(
        user=user1,
        customer_name="customer1",
        city="Berlin",
        phone_number="1111111111",
        total_price="25.00",
        status="pending"
    )

    # Create order for customer2
     Order.objects.create(
        user=user2,
        customer_name="customer2",
        city="Paris",
        phone_number="2222222222",
        total_price="50.00",
        status="pending"
    )

     self.client.force_authenticate(user=user1)

     response = self.client.get("/api/orders/")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)
     self.assertEqual(response.data["results"][0]["customer_name"], "customer1")


    def test_admin_can_see_all_orders(self):
     user1 = User.objects.create_user(
        username="customer1",
        password="customer12345"
    )

     user2 = User.objects.create_user(
        username="customer2",
        password="customer12345"
    )

     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     Order.objects.create(
        user=user1,
        customer_name="customer1",
        city="Berlin",
        phone_number="1111111111",
        total_price="25.00",
        status="pending"
    )

     Order.objects.create(
        user=user2,
        customer_name="customer2",
        city="Paris",
        phone_number="2222222222",
        total_price="50.00",
        status="pending"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.get("/api/orders/")

     self.assertEqual(response.status_code, 200)
     
     self.assertEqual(response.data["count"], 2)

    def test_guest_can_view_products(self):
     response = self.client.get("/api/products/")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)
     self.assertEqual(response.data["results"][0]["name"], "Mouse") 

    def test_guest_cannot_create_product(self):
     response = self.client.post(
        "/api/products/",
        {
            "category": self.category.id,
            "name": "Keyboard",
            "description": "Mechanical keyboard",
            "price": "50.00",
            "stock": 5
        },
        format="json"
    )

     self.assertEqual(response.status_code, 401)

    def test_admin_can_create_product(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(
        "/api/products/",
        {
            "category": self.category.id,
            "name": "Keyboard",
            "description": "Mechanical keyboard",
            "price": "50.00",
            "stock": 5
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)
     self.assertEqual(Product.objects.count(), 2)   


    def test_admin_manual_stock_adjustment_creates_stock_movement(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(
        f"/api/products/{self.product.id}/adjust_stock/",
        {
            "quantity_change": 20,
            "note": "New shipment received"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 200)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 30)

     stock_movement = StockMovement.objects.last()
     self.assertEqual(stock_movement.product, self.product)
     self.assertEqual(stock_movement.quantity_change, 20)
     self.assertEqual(stock_movement.reason, "manual_adjustment")
     self.assertEqual(stock_movement.note, "New shipment received") 

    def test_guest_cannot_adjust_stock(self):
     response = self.client.post(
        f"/api/products/{self.product.id}/adjust_stock/",
        {
            "quantity_change": 20,
            "note": "Unauthorized stock change"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 401)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(StockMovement.objects.count(), 0) 

    def test_admin_can_view_stock_movements(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     StockMovement.objects.create(
        product=self.product,
        quantity_change=10,
        reason="manual_adjustment",
        note="Test movement"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.get("/api/stock-movements/")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)
     self.assertEqual(response.data["results"][0]["quantity_change"], 10)
     self.assertEqual(response.data["results"][0]["reason"], "manual_adjustment")


    def test_guest_cannot_view_stock_movements(self):
     StockMovement.objects.create(
        product=self.product,
        quantity_change=10,
        reason="manual_adjustment",
        note="Test movement"
    )

     response = self.client.get("/api/stock-movements/")

     self.assertEqual(response.status_code, 401)


    def test_customer_cannot_view_stock_movements(self):
     customer = User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     StockMovement.objects.create(
        product=self.product,
        quantity_change=10,
        reason="manual_adjustment",
        note="Test movement"
    )

     self.client.force_authenticate(user=customer)

     response = self.client.get("/api/stock-movements/")

     self.assertEqual(response.status_code, 403) 

    def test_admin_can_view_dashboard_stats(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     Order.objects.create(
        customer_name="Customer 1",
        city="Berlin",
        phone_number="1111111111",
        total_price="25.00",
        status="pending"
    )

     Order.objects.create(
        customer_name="Customer 2",
        city="Paris",
        phone_number="2222222222",
        total_price="50.00",
        status="delivered"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.get("/api/dashboard/stats/")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["total_orders"], 2)
     self.assertEqual(response.data["pending_orders"], 1)
     self.assertEqual(response.data["delivered_orders"], 1) 
     
    def test_guest_cannot_view_dashboard_stats(self):
     response = self.client.get("/api/dashboard/stats/")

     self.assertEqual(response.status_code, 401)

    def test_revenue_report_counts_only_delivered_orders(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     Order.objects.create(
        customer_name="Pending Customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="100.00",
        status="pending"
    )

     Order.objects.create(
        customer_name="Delivered Customer",
        city="Paris",
        phone_number="2222222222",
        total_price="50.00",
        status="delivered"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.get("/api/dashboard/revenue/")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["delivered_orders_count"], 1)
     self.assertEqual(str(response.data["total_revenue"]), "50") 

    def test_admin_can_view_low_stock_products(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     low_stock_product = Product.objects.create(
        category=self.category,
        name="Low Stock Keyboard",
        description="Only few left",
        price="40.00",
        stock=3
    )

     Product.objects.create(
        category=self.category,
        name="High Stock Monitor",
        description="Many available",
        price="150.00",
        stock=20
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.get("/api/dashboard/low-stock/")

     self.assertEqual(response.status_code, 200)

     product_names = [
       product["name"] for product in response.data
      ]

     self.assertIn(low_stock_product.name, product_names)
     self.assertNotIn("High Stock Monitor", product_names) 


    def test_best_selling_products_report(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
     )

     product2 = Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=20
     )

     delivered_order = Order.objects.create(
        customer_name="Delivered Customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="100.00",
        status="delivered"
     )

     pending_order = Order.objects.create(
        customer_name="Pending Customer",
        city="Paris",
        phone_number="2222222222",
        total_price="100.00",
        status="pending"
     )

     OrderItem.objects.create(
        order=delivered_order,
        product=self.product,
        quantity=3
     )

     OrderItem.objects.create(
        order=delivered_order,
        product=product2,
        quantity=1
     )

     OrderItem.objects.create(
        order=pending_order,
        product=product2,
        quantity=10
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.get("/api/dashboard/best-sellers/")

     self.assertEqual(response.status_code, 200)

     products = response.data["products"]

     self.assertEqual(products[0]["product__name"], "Mouse")
     self.assertEqual(products[0]["total_quantity"], 3)

     product_names = [
        product["product__name"] for product in products
     ]

     self.assertIn("Mouse", product_names)
     self.assertIn("Keyboard", product_names)

     keyboard_data = next(
        product for product in products
        if product["product__name"] == "Keyboard"
    )

     self.assertEqual(keyboard_data["total_quantity"], 1)

    def test_manual_stock_adjustment_cannot_make_stock_negative(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(
        f"/api/products/{self.product.id}/adjust_stock/",
        {
            "quantity_change": -20,
            "note": "Trying to remove too much stock"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 400)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(StockMovement.objects.count(), 0) 



    def test_order_creation_fails_when_quantity_exceeds_stock(self):
     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Trying to order more than available stock.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 20
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 400)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(Order.objects.count(), 0)
     self.assertEqual(StockMovement.objects.count(), 0) 

    def test_guest_order_requires_phone_number(self):
     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "notes": "Trying to order without phone number.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 400)
 
     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(Order.objects.count(), 0)
     self.assertEqual(StockMovement.objects.count(), 0) 


    def test_guest_order_requires_city(self):
     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "phone_number": "0123456789",
            "notes": "Trying to order without city.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 400)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(Order.objects.count(), 0)
     self.assertEqual(StockMovement.objects.count(), 0) 

    def test_guest_order_requires_customer_name(self):
     response = self.client.post(
        "/api/orders/",
        {
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Trying to order without customer name.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 400)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(Order.objects.count(), 0)
     self.assertEqual(StockMovement.objects.count(), 0) 

    def test_order_requires_at_least_one_product(self):
     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Trying to create order without products.",
            "order_items": []
        },
        format="json"
    )

     self.assertEqual(response.status_code, 400)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(Order.objects.count(), 0)
     self.assertEqual(StockMovement.objects.count(), 0) 

    def test_customer_order_saves_phone_number_to_profile(self):
     customer = User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     self.client.force_authenticate(user=customer)

     response = self.client.post(
        "/api/orders/",
        {
            "city": "Berlin",
            "phone_number": "0123456789",
            "use_saved_phone": False,
            "notes": "First authenticated customer order.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

    
     self.assertEqual(response.status_code, 201)

     customer.refresh_from_db()
     self.assertEqual(customer.profile.phone_number, "0123456789")
     self.assertEqual(customer.profile.city, "Berlin")

     order = Order.objects.first()
     self.assertEqual(order.user, customer)
     self.assertEqual(order.customer_name, "customer")
     self.assertEqual(order.phone_number, "0123456789")
     self.assertEqual(order.city, "Berlin")

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 9) 

    def test_customer_can_create_order_using_saved_phone_number(self):
     customer = User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     self.client.force_authenticate(user=customer)

     first_response = self.client.post(
        "/api/orders/",
        {
            "city": "Berlin",
            "phone_number": "0123456789",
            "use_saved_phone": False,
            "notes": "First order saves phone number.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                 }
             ]
         },
        format="json"
     )

     self.assertEqual(first_response.status_code, 201)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 9)

     second_response = self.client.post(
        "/api/orders/",
        {
            "use_saved_phone": True,
            "notes": "Second order uses saved phone number.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 2
                }
            ]
        },
        format="json"
     )

     self.assertEqual(second_response.status_code, 201)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 7)

     orders = Order.objects.filter(user=customer).order_by("created_at")
     self.assertEqual(orders.count(), 2)

     second_order = orders.last()
     self.assertEqual(second_order.customer_name, "customer")
     self.assertEqual(second_order.phone_number, "0123456789")
     self.assertEqual(second_order.city, "Berlin") 

    def test_customer_cannot_use_saved_phone_if_no_phone_is_saved(self):
     customer = User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     self.client.force_authenticate(user=customer)

     response = self.client.post(
        "/api/orders/",
        {
            "use_saved_phone": True,
            "notes": "Trying to use saved phone without saved profile phone.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 400)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(Order.objects.count(), 0)
     self.assertEqual(StockMovement.objects.count(), 0) 

    def test_customer_can_update_saved_phone_and_city_with_new_order(self):
     customer = User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     self.client.force_authenticate(user=customer)

     first_response = self.client.post(
        "/api/orders/",
        {
            "city": "Berlin",
            "phone_number": "0123456789",
            "use_saved_phone": False,
            "notes": "First order saves first phone and city.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(first_response.status_code, 201)

     second_response = self.client.post(
        "/api/orders/",
        {
            "city": "Paris",
            "phone_number": "9999999999",
            "use_saved_phone": False,
            "notes": "Second order updates saved phone and city.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 2
                }
            ]
        },
        format="json"
    )

     self.assertEqual(second_response.status_code, 201)

     customer.refresh_from_db()
     self.assertEqual(customer.profile.phone_number, "9999999999")
     self.assertEqual(customer.profile.city, "Paris")

     orders = Order.objects.filter(user=customer).order_by("created_at")
     self.assertEqual(orders.count(), 2)

     second_order = orders.last()
     self.assertEqual(second_order.phone_number, "9999999999")
     self.assertEqual(second_order.city, "Paris")

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 7)

    def test_customer_cannot_view_another_customers_order_detail(self):
     customer1 = User.objects.create_user(
        username="customer1",
        password="customer12345"
    )

     customer2 = User.objects.create_user(
        username="customer2",
        password="customer12345"
    )

     order1 = Order.objects.create(
        user=customer1,
        customer_name="customer1",
        city="Berlin",
        phone_number="1111111111",
        total_price="25.00",
        status="pending"
    )

     Order.objects.create(
        user=customer2,
        customer_name="customer2",
        city="Paris",
        phone_number="2222222222",
        total_price="25.00",
        status="pending"
      )

     self.client.force_authenticate(user=customer2)

     response = self.client.get(f"/api/orders/{order1.id}/")

     self.assertEqual(response.status_code, 404)  

    def test_admin_can_view_any_order_detail(self):
     customer = User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     order = Order.objects.create(
        user=customer,
        customer_name="customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="25.00",
        status="pending"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.get(f"/api/orders/{order.id}/")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["id"], order.id)
     self.assertEqual(response.data["customer_name"], "customer")
     self.assertEqual(response.data["city"], "Berlin")
     self.assertEqual(response.data["phone_number"], "1111111111") 

    def test_customer_cannot_validate_order(self):
     customer = User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     order = Order.objects.create(
        user=customer,
        customer_name="customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="25.00",
        status="pending"
    )

     self.client.force_authenticate(user=customer)

     response = self.client.post(f"/api/orders/{order.id}/validate_order/")

     self.assertEqual(response.status_code, 403)

     order.refresh_from_db()
     self.assertEqual(order.status, "pending") 

    def test_customer_cannot_deliver_order(self):
     customer = User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     order = Order.objects.create(
        user=customer,
        customer_name="customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="25.00",
        status="validated"
    )

     self.client.force_authenticate(user=customer)

     response = self.client.post(f"/api/orders/{order.id}/deliver_order/")

     self.assertEqual(response.status_code, 403)

     order.refresh_from_db()
     self.assertEqual(order.status, "validated") 

    def test_customer_cannot_cancel_order(self):
     customer = User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     order = Order.objects.create(
        user=customer,
        customer_name="customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="25.00",
        status="pending"
    )

     self.client.force_authenticate(user=customer)

     response = self.client.post(f"/api/orders/{order.id}/cancel_order/")

     self.assertEqual(response.status_code, 403)

     order.refresh_from_db()
     self.assertEqual(order.status, "pending")

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10) 

    def test_delivered_order_cannot_be_cancelled(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     order = Order.objects.create(
        customer_name="Delivered Customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="25.00",
        status="delivered"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(f"/api/orders/{order.id}/cancel_order/")

     self.assertEqual(response.status_code, 400)

     order.refresh_from_db()
     self.assertEqual(order.status, "delivered")

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(StockMovement.objects.count(), 0) 

    def test_delivered_order_cannot_be_cancelled(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     order = Order.objects.create(
        customer_name="Delivered Customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="25.00",
        status="delivered"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(f"/api/orders/{order.id}/cancel_order/")

     self.assertEqual(response.status_code, 400)

     order.refresh_from_db()
     self.assertEqual(order.status, "delivered")

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(StockMovement.objects.count(), 0)


    def test_cancelled_order_cannot_be_delivered(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     order = Order.objects.create(
        customer_name="Cancelled Customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="25.00",
        status="cancelled"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(f"/api/orders/{order.id}/deliver_order/")

     self.assertEqual(response.status_code, 400)

     order.refresh_from_db()
     self.assertEqual(order.status, "cancelled")

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(StockMovement.objects.count(), 0) 

    def test_product_search_by_name(self):
     Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=5
    )

     response = self.client.get("/api/products/?search=Mouse")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)
     self.assertEqual(response.data["results"][0]["name"], "Mouse") 

    def test_product_filter_by_category(self):
     second_category = Category.objects.create(name="Accessories")

     Product.objects.create(
        category=second_category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=5
    )

     response = self.client.get(f"/api/products/?category={self.category.id}")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)
     self.assertEqual(response.data["results"][0]["name"], "Mouse")
     self.assertEqual(response.data["results"][0]["category"], self.category.id)

    def test_product_filter_by_min_price(self):
     Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=5
    )

     response = self.client.get("/api/products/?min_price=30")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)
     self.assertEqual(response.data["results"][0]["name"], "Keyboard")


    def test_product_filter_by_max_price(self):
     Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=5
    )

     response = self.client.get("/api/products/?max_price=30")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)
     self.assertEqual(response.data["results"][0]["name"], "Mouse")


    def test_product_filter_by_price_range(self):
     Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=5
    )

     Product.objects.create(
        category=self.category,
        name="Monitor",
        description="HD monitor",
        price="150.00",
        stock=3
    )

     response = self.client.get("/api/products/?min_price=30&max_price=100")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)
     self.assertEqual(response.data["results"][0]["name"], "Keyboard") 

    def test_product_ordering_by_price_ascending(self):
     Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=5
    )

     Product.objects.create(
        category=self.category,
        name="Monitor",
        description="HD monitor",
        price="150.00",
        stock=3
    )

     response = self.client.get("/api/products/?ordering=price")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["results"][0]["name"], "Mouse")
     self.assertEqual(response.data["results"][1]["name"], "Keyboard")
     self.assertEqual(response.data["results"][2]["name"], "Monitor")


    def test_product_ordering_by_price_descending(self):
     Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=5
    )

     Product.objects.create(
        category=self.category,
        name="Monitor",
        description="HD monitor",
        price="150.00",
        stock=3
    )

     response = self.client.get("/api/products/?ordering=-price")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["results"][0]["name"], "Monitor")
     self.assertEqual(response.data["results"][1]["name"], "Keyboard")
     self.assertEqual(response.data["results"][2]["name"], "Mouse")


    def test_product_ordering_by_name(self):
     Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=5
    )

     Product.objects.create(
        category=self.category,
        name="Monitor",
        description="HD monitor",
        price="150.00",
        stock=3
    )

     response = self.client.get("/api/products/?ordering=name")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["results"][0]["name"], "Keyboard")
     self.assertEqual(response.data["results"][1]["name"], "Monitor")
     self.assertEqual(response.data["results"][2]["name"], "Mouse")

    def test_product_search_by_description(self):
     Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=5
    )

     response = self.client.get("/api/products/?search=Mechanical")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)
     self.assertEqual(response.data["results"][0]["name"], "Keyboard")


    def test_product_search_by_category_name(self):
     second_category = Category.objects.create(name="Accessories")

     Product.objects.create(
        category=second_category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=5
    )

     response = self.client.get("/api/products/?search=Accessories")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)
     self.assertEqual(response.data["results"][0]["name"], "Keyboard")


    def test_product_ordering_by_stock(self):
     Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=5
    )

     Product.objects.create(
        category=self.category,
        name="Monitor",
        description="HD monitor",
        price="150.00",
        stock=3
    )

     response = self.client.get("/api/products/?ordering=stock")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["results"][0]["name"], "Monitor")
     self.assertEqual(response.data["results"][1]["name"], "Keyboard")
     self.assertEqual(response.data["results"][2]["name"], "Mouse") 

    def test_order_total_price_is_calculated_from_multiple_products(self):
     product2 = Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=10
    )

     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Order with multiple products.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 2
                },
                {
                    "product": product2.id,
                    "quantity": 3
                }
            ]
        },
        format="json"
     )

     self.assertEqual(response.status_code, 201)

     order = Order.objects.first()

     expected_total = Decimal("25.00") * 2 + Decimal("50.00") * 3
     self.assertEqual(order.total_price, expected_total)
     self.product.refresh_from_db()
     product2.refresh_from_db()

     self.assertEqual(self.product.stock, 8)
     self.assertEqual(product2.stock, 7)

     self.assertEqual(order.items.count(), 2)
     self.assertEqual(StockMovement.objects.count(), 2) 

    def test_full_order_lifecycle_from_pending_to_delivered(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Full lifecycle order.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 2
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)

     order = Order.objects.first()
     self.assertEqual(order.status, "pending")

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 8)

     self.client.force_authenticate(user=admin_user)

     validate_response = self.client.post(
        f"/api/orders/{order.id}/validate_order/"
    )

     self.assertEqual(validate_response.status_code, 200)

     order.refresh_from_db()
     self.assertEqual(order.status, "validated")

     deliver_response = self.client.post(
        f"/api/orders/{order.id}/deliver_order/"
    )

     self.assertEqual(deliver_response.status_code, 200)

     order.refresh_from_db()
     self.assertEqual(order.status, "delivered")

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 8)

     self.assertEqual(order.status_history.count(), 2)

     first_history = order.status_history.first()
     last_history = order.status_history.last()

     self.assertEqual(first_history.old_status, "pending")
     self.assertEqual(first_history.new_status, "validated")

     self.assertEqual(last_history.old_status, "validated")
     self.assertEqual(last_history.new_status, "delivered") 

    def test_revenue_report_filters_by_date_range(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     Order.objects.create(
        customer_name="Old Customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="100.00",
        status="delivered"
    )

     recent_order = Order.objects.create(
        customer_name="Recent Customer",
        city="Paris",
        phone_number="2222222222",
        total_price="50.00",
        status="delivered"
    )

     self.client.force_authenticate(user=admin_user)

     date = recent_order.created_at.date()

     response = self.client.get(
        f"/api/dashboard/revenue/?start_date={date}&end_date={date}"
    )

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["delivered_orders_count"], 2)
     self.assertEqual(str(response.data["total_revenue"]), "150") 

    def test_revenue_report_excludes_orders_outside_date_range(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     old_order = Order.objects.create(
        customer_name="Old Customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="100.00",
        status="delivered"
    )

     recent_order = Order.objects.create(
        customer_name="Recent Customer",
        city="Paris",
        phone_number="2222222222",
        total_price="50.00",
        status="delivered"
    )

     old_order.created_at = timezone.now() - timedelta(days=10)
     old_order.save(update_fields=["created_at"])

     self.client.force_authenticate(user=admin_user)

     today = recent_order.created_at.date()

     response = self.client.get(
        f"/api/dashboard/revenue/?start_date={today}&end_date={today}"
    )

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["delivered_orders_count"], 1)
     self.assertEqual(str(response.data["total_revenue"]), "50") 

    def test_best_selling_products_filters_by_date_range(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     product2 = Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=20
    )

     old_order = Order.objects.create(
        customer_name="Old Customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="75.00",
        status="delivered"
    )

     recent_order = Order.objects.create(
        customer_name="Recent Customer",
        city="Paris",
        phone_number="2222222222",
        total_price="100.00",
        status="delivered"
    )

     pending_order = Order.objects.create(
        customer_name="Pending Customer",
        city="Rome",
        phone_number="3333333333",
        total_price="500.00",
        status="pending"
    )

     old_order.created_at = timezone.now() - timedelta(days=10)
     old_order.save(update_fields=["created_at"])

     OrderItem.objects.create(
        order=old_order,
        product=product2,
        quantity=5
    )

     OrderItem.objects.create(
        order=recent_order,
        product=self.product,
        quantity=3
    )

     OrderItem.objects.create(
        order=pending_order,
        product=product2,
        quantity=10
    )

     self.client.force_authenticate(user=admin_user)

     today = recent_order.created_at.date()

     response = self.client.get(
        f"/api/dashboard/best-sellers/?start_date={today}&end_date={today}"
    )

     self.assertEqual(response.status_code, 200)

     products = response.data["products"]

     self.assertEqual(len(products), 1)
     self.assertEqual(products[0]["product__name"], "Mouse")
     self.assertEqual(products[0]["total_quantity"], 3)


    def test_best_selling_products_ignores_pending_orders(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     product2 = Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=20
    )

     delivered_order = Order.objects.create(
        customer_name="Delivered Customer",
        city="Berlin",
        phone_number="1111111111",
        total_price="75.00",
        status="delivered"
    )

     pending_order = Order.objects.create(
        customer_name="Pending Customer",
        city="Paris",
        phone_number="2222222222",
        total_price="500.00",
        status="pending"
    )

     OrderItem.objects.create(
        order=delivered_order,
        product=self.product,
        quantity=3
    )

     OrderItem.objects.create(
        order=pending_order,
        product=product2,
        quantity=10
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.get("/api/dashboard/best-sellers/")

     self.assertEqual(response.status_code, 200)

     products = response.data["products"]
     product_names = [product["product__name"] for product in products]

     self.assertIn("Mouse", product_names)
     self.assertNotIn("Keyboard", product_names)

     mouse_data = next(
        product for product in products
        if product["product__name"] == "Mouse"
    )

     self.assertEqual(mouse_data["total_quantity"], 3) 

    def test_order_creation_creates_stock_movements_linked_to_order_and_product(self):
     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Testing stock movement links.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 2
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)

     order = Order.objects.first()
     movement = StockMovement.objects.first()

     self.assertIsNotNone(movement)
     self.assertEqual(movement.product, self.product)
     self.assertEqual(movement.order, order)
     self.assertEqual(movement.quantity_change, -2)
     self.assertEqual(movement.reason, "order_created")
 
     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 8) 

    def test_cancel_order_creates_stock_movement_linked_to_order_and_product(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Order that will be cancelled.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 2
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)

     order = Order.objects.first()

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 8)

     self.client.force_authenticate(user=admin_user)

     cancel_response = self.client.post(
        f"/api/orders/{order.id}/cancel_order/"
    )

     self.assertEqual(cancel_response.status_code, 200)

     order.refresh_from_db()
     self.assertEqual(order.status, "cancelled")

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     movements = StockMovement.objects.filter(order=order).order_by("created_at")

     self.assertEqual(movements.count(), 2)
 
     cancel_movement = movements.last()

     self.assertEqual(cancel_movement.product, self.product)
     self.assertEqual(cancel_movement.order, order)
     self.assertEqual(cancel_movement.quantity_change, 2)
     self.assertEqual(cancel_movement.reason, "order_cancelled") 

    def test_manual_stock_adjustment_creates_stock_movement_without_order(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(
        f"/api/products/{self.product.id}/adjust_stock/",
        {
            "quantity_change": 5,
            "note": "Manual restock from supplier"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 200)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 15)
 
     movement = StockMovement.objects.first()

     self.assertIsNotNone(movement)
     self.assertEqual(movement.product, self.product)
     self.assertIsNone(movement.order)
     self.assertEqual(movement.quantity_change, 5)
     self.assertEqual(movement.reason, "manual_adjustment")
     self.assertEqual(movement.note, "Manual restock from supplier") 

    def test_stock_movement_api_returns_movement_details(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     StockMovement.objects.create(
        product=self.product,
        quantity_change=5,
        reason="manual_adjustment",
        note="Supplier restock"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.get("/api/stock-movements/")

     self.assertEqual(response.status_code, 200)

     self.assertEqual(response.data["count"], 1)

     movement = response.data["results"][0]

     self.assertEqual(movement["product"], self.product.id)
     self.assertEqual(movement["quantity_change"], 5)
     self.assertEqual(movement["reason"], "manual_adjustment")
     self.assertEqual(movement["note"], "Supplier restock") 

    def test_stock_movements_are_ordered_newest_first(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     first_movement = StockMovement.objects.create(
        product=self.product,
        quantity_change=5,
        reason="manual_adjustment",
        note="First movement"
    )

     second_movement = StockMovement.objects.create(
        product=self.product,
        quantity_change=-2,
        reason="manual_adjustment",
        note="Second movement"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.get("/api/stock-movements/")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 2)

     self.assertEqual(response.data["results"][0]["note"], "Second movement")
     self.assertEqual(response.data["results"][1]["note"], "First movement") 

    def test_stock_movements_can_be_filtered_by_product(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     product2 = Product.objects.create(
        category=self.category,
        name="Keyboard",
        description="Mechanical keyboard",
        price="50.00",
        stock=10
    )

     StockMovement.objects.create(
        product=self.product,
        quantity_change=5,
        reason="manual_adjustment",
        note="Mouse restock"
    )

     StockMovement.objects.create(
        product=product2,
        quantity_change=3,
        reason="manual_adjustment",
        note="Keyboard restock"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.get(f"/api/stock-movements/?product={self.product.id}")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)

     stock_movement = response.data["results"][0]

     self.assertEqual(stock_movement["product"], self.product.id)
     self.assertEqual(stock_movement["note"], "Mouse restock") 

    def test_stock_movements_can_be_filtered_by_reason(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     StockMovement.objects.create(
        product=self.product,
        quantity_change=5,
        reason="manual_adjustment",
        note="Manual stock update"
    )

     StockMovement.objects.create(
        product=self.product,
        quantity_change=-2,
        reason="order_created",
        note="Order stock decrease"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.get(
        "/api/stock-movements/?reason=manual_adjustment"
    )

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)

     stock_movement = response.data["results"][0]

     self.assertEqual(stock_movement["reason"], "manual_adjustment")
     self.assertEqual(stock_movement["quantity_change"], 5)
     self.assertEqual(stock_movement["note"], "Manual stock update") 

    def test_manual_stock_adjustment_requires_quantity_change(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(
        f"/api/products/{self.product.id}/adjust_stock/",
        {
            "note": "Missing quantity change"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 400)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(StockMovement.objects.count(), 0) 

    def test_manual_stock_adjustment_requires_integer_quantity_change(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(
        f"/api/products/{self.product.id}/adjust_stock/",
        {
            "quantity_change": "abc",
            "note": "Invalid quantity change"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 400)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(StockMovement.objects.count(), 0) 




    def test_manual_stock_adjustment_allows_positive_quantity_change(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(
        f"/api/products/{self.product.id}/adjust_stock/",
        {
            "quantity_change": 10,
            "note": "Supplier restock"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 200)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 20)

     stock_movement = StockMovement.objects.first()

     self.assertEqual(stock_movement.product, self.product)
     self.assertEqual(stock_movement.quantity_change, 10)
     self.assertEqual(stock_movement.reason, "manual_adjustment")
     self.assertEqual(stock_movement.note, "Supplier restock")


    def test_manual_stock_adjustment_allows_negative_quantity_if_stock_remains_positive(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(
        f"/api/products/{self.product.id}/adjust_stock/",
        {
            "quantity_change": -3,
            "note": "Damaged items removed"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 200)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 7)

     stock_movement = StockMovement.objects.first()

     self.assertEqual(stock_movement.product, self.product)
     self.assertEqual(stock_movement.quantity_change, -3)
     self.assertEqual(stock_movement.reason, "manual_adjustment")
     self.assertEqual(stock_movement.note, "Damaged items removed")


    def test_guest_cannot_create_category(self):
     response = self.client.post(
        "/api/categories/",
        {
            "name": "New Category"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 401)
     self.assertEqual(Category.objects.count(), 1)


    def test_customer_cannot_create_category(self):
     customer = User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     self.client.force_authenticate(user=customer)

     response = self.client.post(
        "/api/categories/",
        {
            "name": "New Category"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 403)
     self.assertEqual(Category.objects.count(), 1)


    def test_admin_can_create_category(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(
        "/api/categories/",
        {
            "name": "Accessories"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)
     self.assertEqual(Category.objects.count(), 2)
     self.assertTrue(Category.objects.filter(name="Accessories").exists())


    def test_order_response_contains_status_history(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Order status history test.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)

     order = Order.objects.first()

     self.client.force_authenticate(user=admin_user)

     validate_response = self.client.post(
        f"/api/orders/{order.id}/validate_order/"
    )

     self.assertEqual(validate_response.status_code, 200)

     detail_response = self.client.get(f"/api/orders/{order.id}/")

     self.assertEqual(detail_response.status_code, 200)
     self.assertIn("status_history", detail_response.data)
     self.assertEqual(len(detail_response.data["status_history"]), 1)
     self.assertEqual(
        detail_response.data["status_history"][0]["old_status"],
        "pending"
    )
     self.assertEqual(
        detail_response.data["status_history"][0]["new_status"],
        "validated"
    )


    def test_admin_can_create_product_with_image(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     image = SimpleUploadedFile(
        name="test_image.jpg",
        content=(
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00"
            b"\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21"
            b"\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00"
            b"\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c"
            b"\x01\x00\x3b"
        ),
        content_type="image/gif"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(
        "/api/products/",
        {
            "category": self.category.id,
            "name": "Product With Image",
            "description": "Product image upload test.",
            "price": "99.99",
            "stock": 5,
            "image": image
        },
        format="multipart"
    )

     self.assertEqual(response.status_code, 201)

     product = Product.objects.get(name="Product With Image")

     self.assertIsNotNone(product.image)
     self.assertEqual(product.stock, 5)
     self.assertEqual(str(product.price), "99.99")

    def test_user_can_register(self):
     response = self.client.post(
        "/api/register/",
        {
            "username": "newcustomer",
            "email": "newcustomer@example.com",
            "password": "customer12345",
            "password_confirm": "customer12345"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)
     self.assertTrue(User.objects.filter(username="newcustomer").exists())

     user = User.objects.get(username="newcustomer")
     self.assertEqual(user.email, "newcustomer@example.com")
     self.assertTrue(user.check_password("customer12345"))


    def test_register_fails_when_passwords_do_not_match(self):
     response = self.client.post(
        "/api/register/",
        {
            "username": "newcustomer",
            "email": "newcustomer@example.com",
            "password": "customer12345",
            "password_confirm": "wrongpassword"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 400)
     self.assertFalse(User.objects.filter(username="newcustomer").exists())


    def test_register_fails_when_username_already_exists(self):
     User.objects.create_user(
        username="newcustomer",
        email="old@example.com",
        password="customer12345"
    )

     response = self.client.post(
         "/api/register/",
        {
            "username": "newcustomer",
            "email": "new@example.com",
            "password": "customer12345",
            "password_confirm": "customer12345"
        },
        format="json"
    )
 
     self.assertEqual(response.status_code, 400)
     self.assertEqual(User.objects.filter(username="newcustomer").count(), 1)


    def test_user_can_login_and_receive_jwt_tokens(self):
     User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     response = self.client.post(
        "/api/token/",
        {
            "username": "customer",
            "password": "customer12345"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 200)
     self.assertIn("access", response.data)
     self.assertIn("refresh", response.data)


    def test_user_cannot_login_with_wrong_password(self):
     User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     response = self.client.post(
        "/api/token/",
        {
            "username": "customer",
            "password": "wrongpassword"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 401)
     self.assertNotIn("access", response.data)
     self.assertNotIn("refresh", response.data) 

    def test_user_can_refresh_access_token(self):
     User.objects.create_user(
        username="customer",
        password="customer12345"
     )

     login_response = self.client.post(
        "/api/token/",
        {
            "username": "customer",
            "password": "customer12345"
        },
        format="json"
    )

     self.assertEqual(login_response.status_code, 200)

     refresh_token = login_response.data["refresh"]

     refresh_response = self.client.post(
        "/api/token/refresh/",
        {
            "refresh": refresh_token
        },
        format="json"
    )

     self.assertEqual(refresh_response.status_code, 200)
     self.assertIn("access", refresh_response.data)

    def test_customer_can_create_order_with_jwt_token(self):
     User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     login_response = self.client.post(
        "/api/token/",
        {
            "username": "customer",
            "password": "customer12345"
        },
        format="json"
    )

     self.assertEqual(login_response.status_code, 200)

     access_token = login_response.data["access"]

     self.client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {access_token}"
    )

     response = self.client.post(
        "/api/orders/",
        {
            "city": "Berlin",
            "phone_number": "0123456789",
            "use_saved_phone": False,
            "notes": "Order created using JWT token.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(response.status_code, 201)
 
     order = Order.objects.first()

     self.assertEqual(order.user.username, "customer")
     self.assertEqual(order.customer_name, "customer")
     self.assertEqual(order.phone_number, "0123456789")
     self.assertEqual(order.city, "Berlin")

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 9) 

    def test_customer_can_use_saved_phone_with_jwt_token(self):
     User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     login_response = self.client.post(
        "/api/token/",
        {
            "username": "customer",
            "password": "customer12345"
        },
        format="json"
    )

     self.assertEqual(login_response.status_code, 200)

     access_token = login_response.data["access"]

     self.client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {access_token}"
    )

     first_response = self.client.post(
        "/api/orders/",
        {
            "city": "Berlin",
            "phone_number": "0123456789",
            "use_saved_phone": False,
            "notes": "First JWT order saves phone.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 1
                }
            ]
        },
        format="json"
    )

     self.assertEqual(first_response.status_code, 201)

     second_response = self.client.post(
        "/api/orders/",
        {
            "use_saved_phone": True,
            "notes": "Second JWT order uses saved phone.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 2
                }
            ]
        },
        format="json"
    )

     self.assertEqual(second_response.status_code, 201)

     orders = Order.objects.filter(user__username="customer").order_by("created_at")
     self.assertEqual(orders.count(), 2)

     second_order = orders.last()
     self.assertEqual(second_order.phone_number, "0123456789")
     self.assertEqual(second_order.city, "Berlin")

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 7) 

    def test_invalid_jwt_token_cannot_access_orders(self):
     self.client.credentials(
        HTTP_AUTHORIZATION="Bearer invalidtoken123"
    )

     response = self.client.get("/api/orders/")

     self.assertEqual(response.status_code, 401) 

    def test_guest_order_list_returns_empty_results(self):
     response = self.client.get("/api/orders/")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 0)
     self.assertEqual(response.data["results"], []) 

    def test_admin_can_validate_order_with_jwt_token(self):
     User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     order = Order.objects.create(
        customer_name="Test Customer",
        city="Berlin",
        phone_number="0123456789",
        total_price="25.00",
        status="pending"
    )

     login_response = self.client.post(
        "/api/token/",
        {
            "username": "admin",
            "password": "admin12345"
        },
        format="json"
    )

     self.assertEqual(login_response.status_code, 200)

     access_token = login_response.data["access"]

     self.client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {access_token}"
    )

     response = self.client.post(
        f"/api/orders/{order.id}/validate_order/"
    )

     self.assertEqual(response.status_code, 200)

     order.refresh_from_db()
     self.assertEqual(order.status, "validated")

     self.assertEqual(order.status_history.count(), 1)

     history = order.status_history.first()
     self.assertEqual(history.old_status, "pending")
     self.assertEqual(history.new_status, "validated")
     self.assertEqual(history.changed_by.username, "admin") 

    def test_customer_cannot_validate_order_with_jwt_token(self):
     User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     order = Order.objects.create(
        customer_name="Test Customer",
        city="Berlin",
        phone_number="0123456789",
        total_price="25.00",
        status="pending"
    )

     login_response = self.client.post(
        "/api/token/",
        {
            "username": "customer",
            "password": "customer12345"
        },
        format="json"
    )

     self.assertEqual(login_response.status_code, 200)

     access_token = login_response.data["access"]

     self.client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {access_token}"
    )

     response = self.client.post(
        f"/api/orders/{order.id}/validate_order/"
    )

     self.assertEqual(response.status_code, 403)

     order.refresh_from_db()
     self.assertEqual(order.status, "pending")

     self.assertEqual(order.status_history.count(), 0)  

    def test_customer_cannot_deliver_order_with_jwt_token(self):
     User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     order = Order.objects.create(
        customer_name="Test Customer",
        city="Berlin",
        phone_number="0123456789",
        total_price="25.00",
        status="validated"
    )

     login_response = self.client.post(
        "/api/token/",
        {
            "username": "customer",
            "password": "customer12345"
        },
        format="json"
    )

     self.assertEqual(login_response.status_code, 200)

     access_token = login_response.data["access"]

     self.client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {access_token}"
    )

     response = self.client.post(
        f"/api/orders/{order.id}/deliver_order/"
    )

     self.assertEqual(response.status_code, 403)

     order.refresh_from_db()
     self.assertEqual(order.status, "validated")

     self.assertEqual(order.status_history.count(), 0) 

    def test_customer_cannot_cancel_order_with_jwt_token(self):
     User.objects.create_user(
        username="customer",
        password="customer12345"
    )

     order = Order.objects.create(
        customer_name="Test Customer",
        city="Berlin",
        phone_number="0123456789",
        total_price="25.00",
        status="pending"
    )

     login_response = self.client.post(
        "/api/token/",
        {
            "username": "customer",
            "password": "customer12345"
        },
        format="json"
    )

     self.assertEqual(login_response.status_code, 200)

     access_token = login_response.data["access"]

     self.client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {access_token}"
    )

     response = self.client.post(
        f"/api/orders/{order.id}/cancel_order/"
    )

     self.assertEqual(response.status_code, 403)

     order.refresh_from_db()
     self.assertEqual(order.status, "pending")
     self.assertEqual(order.status_history.count(), 0)


    def test_admin_can_deliver_order_with_jwt_token(self):
     User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     order = Order.objects.create(
        customer_name="Test Customer",
        city="Berlin",
        phone_number="0123456789",
        total_price="25.00",
        status="validated"
    )

     login_response = self.client.post(
        "/api/token/",
        {
            "username": "admin",
            "password": "admin12345"
        },
        format="json"
    )

     self.assertEqual(login_response.status_code, 200)

     access_token = login_response.data["access"]

     self.client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {access_token}"
    )

     response = self.client.post(
        f"/api/orders/{order.id}/deliver_order/"
    )

     self.assertEqual(response.status_code, 200)

     order.refresh_from_db()
     self.assertEqual(order.status, "delivered")

     self.assertEqual(order.status_history.count(), 1)

     history = order.status_history.first()
     self.assertEqual(history.old_status, "validated")
     self.assertEqual(history.new_status, "delivered")
     self.assertEqual(history.changed_by.username, "admin")


    def test_admin_can_cancel_order_with_jwt_token(self):
     User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     order_response = self.client.post(
        "/api/orders/",
        {
            "customer_name": "Test Customer",
            "city": "Berlin",
            "phone_number": "0123456789",
            "notes": "Order to cancel with JWT.",
            "order_items": [
                {
                    "product": self.product.id,
                    "quantity": 2
                }
            ]
        },
        format="json"
    )

     self.assertEqual(order_response.status_code, 201)

     order = Order.objects.first()

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 8)

     login_response = self.client.post(
        "/api/token/",
        {
            "username": "admin",
            "password": "admin12345"
        },
        format="json"
    )

     self.assertEqual(login_response.status_code, 200)

     access_token = login_response.data["access"]

     self.client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {access_token}"
    )

     response = self.client.post(
        f"/api/orders/{order.id}/cancel_order/"
    )

     self.assertEqual(response.status_code, 200)

     order.refresh_from_db()
     self.assertEqual(order.status, "cancelled")

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(order.status_history.count(), 1)

     history = order.status_history.first()
     self.assertEqual(history.old_status, "pending")
     self.assertEqual(history.new_status, "cancelled")
     self.assertEqual(history.changed_by.username, "admin")


    def test_customer_with_jwt_can_only_see_own_orders(self):
     customer1 = User.objects.create_user(
        username="customer1",
        password="customer12345"
    )

     customer2 = User.objects.create_user(
        username="customer2",
        password="customer12345"
    )

     Order.objects.create(
        user=customer1,
        customer_name="customer1",
        city="Berlin",
        phone_number="1111111111",
        total_price="25.00",
        status="pending"
    )

     Order.objects.create(
        user=customer2,
        customer_name="customer2",
        city="Paris",
        phone_number="2222222222",
        total_price="50.00",
        status="pending"
    )

     login_response = self.client.post(
        "/api/token/",
        {
            "username": "customer1",
            "password": "customer12345"
        },
        format="json"
    )

     self.assertEqual(login_response.status_code, 200)

     access_token = login_response.data["access"]

     self.client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {access_token}"
    )

     response = self.client.get("/api/orders/")

     self.assertEqual(response.status_code, 200)
     self.assertEqual(response.data["count"], 1)
     self.assertEqual(response.data["results"][0]["customer_name"], "customer1")

    def test_admin_cannot_update_stock_directly_from_product_detail(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.patch(
        f"/api/products/{self.product.id}/",
        {
            "stock": 50
        },
        format="json"
    )

     self.assertEqual(response.status_code, 400)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 10)

     self.assertEqual(StockMovement.objects.count(), 0)  

    def test_admin_can_update_stock_using_adjust_stock_endpoint(self):
     admin_user = User.objects.create_superuser(
        username="admin",
        password="admin12345"
    )

     self.client.force_authenticate(user=admin_user)

     response = self.client.post(
        f"/api/products/{self.product.id}/adjust_stock/",
        {
            "quantity_change": 40,
            "note": "Correct stock update endpoint"
        },
        format="json"
    )

     self.assertEqual(response.status_code, 200)

     self.product.refresh_from_db()
     self.assertEqual(self.product.stock, 50)

     self.assertEqual(StockMovement.objects.count(), 1)

     stock_movement = StockMovement.objects.first()
     self.assertEqual(stock_movement.product, self.product)
     self.assertEqual(stock_movement.quantity_change, 40)
     self.assertEqual(stock_movement.reason, "manual_adjustment")
     self.assertEqual(stock_movement.note, "Correct stock update endpoint") 