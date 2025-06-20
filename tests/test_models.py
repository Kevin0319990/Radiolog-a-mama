from tests.base import BaseTestCase
from inventory_app.models import db, User, Product, InventoryMovement
import datetime

class TestModelCreation(BaseTestCase):

    def test_user_creation(self):
        u = User(username='john', email='john@example.com', role='user')
        u.set_password('cat')
        db.session.add(u)
        db.session.commit()
        self.assertEqual(User.query.count(), 1)
        self.assertTrue(u.check_password('cat'))
        self.assertFalse(u.check_password('dog'))
        self.assertEqual(u.role, 'user')

    def test_product_creation(self):
        p = Product(name='TestBook', description='A book for testing', quantity=100, price=19.99, sku='TB001')
        db.session.add(p)
        db.session.commit()
        self.assertEqual(Product.query.count(), 1)
        self.assertEqual(Product.query.first().name, 'TestBook')
        self.assertEqual(Product.query.first().quantity, 100)

    def test_inventory_movement_creation(self):
        # Create a user and a product first
        user = User(username='mover', email='mover@example.com')
        user.set_password('secure')
        db.session.add(user)

        product = Product(name='Movable Item', quantity=50, price=10.00)
        db.session.add(product)
        db.session.commit() # Commit to get IDs

        movement = InventoryMovement(
            product_id=product.id,
            user_id=user.id,
            quantity_change=10,
            movement_type='stock_entry',
            notes='Initial stock via test'
        )
        db.session.add(movement)
        db.session.commit()

        self.assertEqual(InventoryMovement.query.count(), 1)
        queried_movement = InventoryMovement.query.first()
        self.assertEqual(queried_movement.product_id, product.id)
        self.assertEqual(queried_movement.user_id, user.id)
        self.assertEqual(queried_movement.quantity_change, 10)
        self.assertEqual(queried_movement.movement_type, 'stock_entry')

        # Test relationships (optional here, more for integration tests)
        self.assertEqual(queried_movement.product.name, 'Movable Item')
        self.assertEqual(queried_movement.user.username, 'mover')

    def test_product_default_dates(self):
        p = Product(name='Dated Product', quantity=5, price=1.00)
        db.session.add(p)
        db.session.commit()
        self.assertIsNotNone(p.date_added)
        self.assertIsNotNone(p.last_updated)
        self.assertAlmostEqual(p.date_added, datetime.datetime.utcnow(), delta=datetime.timedelta(seconds=5))
        self.assertAlmostEqual(p.last_updated, datetime.datetime.utcnow(), delta=datetime.timedelta(seconds=5))

    def test_user_default_dates(self):
        u = User(username='dateuser', email='dateuser@example.com')
        u.set_password('password')
        db.session.add(u)
        db.session.commit()
        self.assertIsNotNone(u.date_created)
        self.assertAlmostEqual(u.date_created, datetime.datetime.utcnow(), delta=datetime.timedelta(seconds=5))

    def test_inventory_movement_default_timestamp(self):
        user = User(username='timeuser', email='time@example.com')
        user.set_password('pw')
        product = Product(name='Timed Product', quantity=1, price=1)
        db.session.add_all([user, product])
        db.session.commit()

        movement = InventoryMovement(product_id=product.id, user_id=user.id, quantity_change=1, movement_type='test')
        db.session.add(movement)
        db.session.commit()
        self.assertIsNotNone(movement.timestamp)
        self.assertAlmostEqual(movement.timestamp, datetime.datetime.utcnow(), delta=datetime.timedelta(seconds=5))

if __name__ == '__main__':
    unittest.main()
