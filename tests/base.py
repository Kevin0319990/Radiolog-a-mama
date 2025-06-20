import unittest
import sys
import os

# Ensure the project root (/app) is in sys.path
# This is crucial for 'from inventory_app.app import app' to work
# when tests are run from the /app directory.
if os.getcwd() == '/app':
    sys.path.insert(0, '/app')
else:
    # Fallback if CWD is not /app, though test execution context should be /app
    # This might happen if tests are run from within the /app/tests directory itself
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Import create_app from the inventory_app package (__init__.py)
from inventory_app import create_app, db # db is also exposed from __init__
from inventory_app.models import User, Product, InventoryMovement # Models themselves
from flask import url_for # Import url_for

# from inventory_app.config import TestingConfig # Not needed if create_app handles config


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test variables."""
        self.app = create_app('test') # Corrected: 'test' instead of 'testing'
        self.client = self.app.test_client()

        # Establish an application context before running the tests.
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create all database tables
        db.create_all()

    def tearDown(self):
        """Executed after each test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # Helper methods for tests
    def register_user(self, username="testuser", email="test@example.com", password="password"):
        # url_for needs app context, or use direct path if SERVER_NAME is not set for tests
        # With app_context pushed in setUp, url_for should work.
        return self.client.post(url_for('main.register'), data=dict(
            username=username,
            email=email,
            password=password,
            confirm_password=password
        ), follow_redirects=True)

    def login_user(self, email_or_username="test@example.com", password="password"):
        return self.client.post(url_for('main.login'), data=dict(
            email_or_username=email_or_username,
            password=password,
            remember=False
        ), follow_redirects=True)

    def logout_user(self):
        return self.client.get(url_for('main.logout'), follow_redirects=True)

    def create_admin_user(self, username="adminuser", email="admin@example.com", password="password"):
        admin = User(username=username, email=email, role='admin')
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        return admin

    def create_product(self, name="Test Product", quantity=10, price=9.99, sku="TP001"):
        product = Product(name=name, quantity=quantity, price=price, sku=sku)
        db.session.add(product)
        db.session.commit()
        return product

if __name__ == '__main__':
    unittest.main()
