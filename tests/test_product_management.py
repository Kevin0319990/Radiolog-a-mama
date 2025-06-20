from tests.base import BaseTestCase
from inventory_app.models import Product, User, db
from flask import url_for

class TestProductManagement(BaseTestCase):

    def test_view_products_unauthenticated(self):
        response = self.client.get(url_for('main.products'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please log in to access this page', response.data)

    def test_view_products_authenticated_user(self):
        self.register_user(username="prodviewer", email="viewer@example.com", password="password")
        self.login_user(email_or_username="viewer@example.com", password="password")

        # Create some products to view
        self.create_product(name="Book A", quantity=10, price=5.00, sku="SKUBOOKA")
        self.create_product(name="Pen B", quantity=5, price=1.00, sku="SKUPENB")

        response = self.client.get(url_for('main.products'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Gestión de Productos', response.data.decode('utf-8')) # Gestión
        self.assertIn('Book A', response.data.decode('utf-8'))
        self.assertIn('Pen B', response.data.decode('utf-8'))
        # Regular user should not see "Agregar Nuevo Producto" button
        self.assertNotIn(b'Agregar Nuevo Producto', response.data)
        # Regular user should not see action buttons like Edit/Delete
        self.assertNotIn(b'fas fa-edit', response.data) # Icon for edit

    def test_view_products_authenticated_admin(self):
        admin = self.create_admin_user()
        self.login_user(email_or_username=admin.email, password="password")

        self.create_product(name="Admin Book", quantity=10, price=5.00)
        response = self.client.get(url_for('main.products'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin Book', response.data)
        # Admin should see "Agregar Nuevo Producto" button
        self.assertIn(b'Agregar Nuevo Producto', response.data)
        # Admin should see action buttons
        self.assertIn(b'fas fa-edit', response.data) # Edit icon
        self.assertIn(b'fas fa-trash', response.data) # Delete icon

    def test_add_product_admin(self):
        admin = self.create_admin_user()
        self.login_user(email_or_username=admin.email, password="password")

        response = self.client.post(url_for('main.add_product'), data=dict(
            name="New Awesome Product",
            description="A very cool product",
            quantity="50",
            price="25.99",
            sku="NAP001",
            category="Cool Stuff",
            supplier="Test Supplier Inc."
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200) # Redirects to products page
        self.assertIn(b'Product added successfully!', response.data)
        self.assertIn(b'New Awesome Product', response.data) # Check if it's on the products page

        product = Product.query.filter_by(sku="NAP001").first()
        self.assertIsNotNone(product)
        self.assertEqual(product.name, "New Awesome Product")
        self.assertEqual(product.quantity, 50)
        # Check if initial stock movement was created
        self.assertTrue(product.movements.count() > 0)
        self.assertEqual(product.movements.first().quantity_change, 50)
        self.assertEqual(product.movements.first().movement_type, "initial_stock")


    def test_add_product_regular_user_forbidden(self):
        self.register_user(username="nonadmin", email="nonadmin@example.com", password="password")
        self.login_user(email_or_username="nonadmin@example.com", password="password")

        response = self.client.get(url_for('main.add_product'), follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirects to index
        self.assertIn(b'You do not have permission to access this page.', response.data)

        response_post = self.client.post(url_for('main.add_product'), data=dict(name="Attempted Product"), follow_redirects=True)
        self.assertEqual(response_post.status_code, 200) # Redirects to index
        self.assertIn(b'You do not have permission to access this page.', response_post.data)
        self.assertIsNone(Product.query.filter_by(name="Attempted Product").first())

    def test_edit_product_admin(self):
        admin = self.create_admin_user()
        self.login_user(email_or_username=admin.email, password="password")
        product = self.create_product(name="Editable Product", quantity=10, price=10.00, sku="EP001")

        response = self.client.post(url_for('main.edit_product', product_id=product.id), data=dict(
            name="Edited Awesome Product",
            description=product.description,
            quantity="5", # Changed quantity from 10 to 5
            price="12.50", # Changed price
            sku=product.sku, # Keep SKU same for this test
            category=product.category,
            supplier=product.supplier
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200) # Redirects to products page
        self.assertIn(b'Product updated successfully!', response.data)
        self.assertIn(b'Edited Awesome Product', response.data)

        updated_product = Product.query.get(product.id)
        self.assertEqual(updated_product.name, "Edited Awesome Product")
        self.assertEqual(updated_product.quantity, 5)
        self.assertEqual(updated_product.price, 12.50)

        # Check if inventory movement was created for quantity change
        movement = updated_product.movements.filter_by(movement_type="adjustment_edit").first()
        self.assertIsNotNone(movement)
        self.assertEqual(movement.quantity_change, -5) # 5 - 10 = -5

    def test_delete_product_admin(self):
        admin = self.create_admin_user()
        self.login_user(email_or_username=admin.email, password="password")
        product = self.create_product(name="Deletable Product", sku="DP001")
        product_id = product.id

        response = self.client.post(url_for('main.delete_product', product_id=product_id), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Product deleted successfully!', response.data)
        self.assertIsNone(Product.query.get(product_id))
        # Note: Test for cascading deletes or handling of InventoryMovements related to deleted product might be needed.
        # For now, assuming hard delete is fine.

    def test_product_low_stock_highlighting_and_summary(self):
        # This test combines viewing products with the low stock feature
        app_config = self.client.application.config
        original_threshold = app_config['LOW_STOCK_THRESHOLD']
        app_config['LOW_STOCK_THRESHOLD'] = 5 # Set for test predictability

        user = self.register_user(email="summary@test.com")
        self.login_user(email_or_username="summary@test.com")

        self.create_product(name="Full Stock Product", quantity=20, sku="FS001")
        self.create_product(name="Low Stock Product", quantity=3, sku="LS001") # Below threshold 5
        self.create_product(name="Out of Stock Product", quantity=0, sku="OOS001") # Critical

        response = self.client.get(url_for('main.products'))
        self.assertEqual(response.status_code, 200)
        decoded_data = response.data.decode('utf-8')

        # Check summary stats (these are approximates as exact HTML structure isn't checked)
        self.assertIn('Total de Productos Únicos (Tipos):</strong> 3', decoded_data) # Únicos
        self.assertIn('Total de Unidades en Inventario:</strong> 23', decoded_data) # 20 + 3 + 0

        # Check highlighting
        self.assertIn(b'Out of Stock Product', response.data)
        self.assertIn(b'table-danger critical-stock', response.data) # Class for out of stock
        self.assertIn(b'badge-danger">Agotado</span>', response.data) # Badge for out of stock

        self.assertIn(b'Low Stock Product', response.data)
        self.assertIn(b'table-warning low-stock', response.data) # Class for low stock
        self.assertIn(b'badge-warning">Bajo Stock</span>', response.data) # Badge for low stock

        self.assertIn(b'Full Stock Product', response.data)
        # Ensure Full Stock Product does not have warning/danger classes directly associated in its part of HTML
        # This is harder to test precisely without parsing HTML, but basic check:
        self.assertTrue(response.data.find(b'Full Stock Product') < response.data.find(b'Low Stock Product'))


        app_config['LOW_STOCK_THRESHOLD'] = original_threshold # Reset


if __name__ == '__main__':
    unittest.main()
