from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import datetime
from sqlalchemy import MetaData

# Convention for naming constraints
# See: https://alembic.sqlalchemy.org/en/latest/naming.html
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

# db object will be imported from inventory_app package (__init__.py)
# This avoids creating a new SQLAlchemy instance here.
# The instance in __init__.py will be initialized with the app.
from . import db # Import db from __init__.py of the current package

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256)) # Increased length for future hash algo
    role = db.Column(db.String(20), default='user', nullable=False) # 'user' or 'admin'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False, default=0.0) # Consider using Numeric or Decimal for currency
    sku = db.Column(db.String(50), unique=True, nullable=True) # Stock Keeping Unit
    category = db.Column(db.String(100), nullable=True)
    supplier = db.Column(db.String(100), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name}>'

class InventoryMovement(db.Model):
    __tablename__ = 'inventory_movement'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # User who made the change
    quantity_change = db.Column(db.Integer, nullable=False) # Positive for entry, negative for exit
    movement_type = db.Column(db.String(50), nullable=False) # e.g., 'initial_stock','stock_entry', 'sale', 'return', 'damage_loss', 'adjustment'
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    reference_id = db.Column(db.String(100), nullable=True) # e.g., order ID for a sale, shipment ID for entry

    product = db.relationship('Product', backref=db.backref('movements', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('inventory_actions', lazy='dynamic'))

    def __repr__(self):
        return f'<InventoryMovement {self.movement_type} for Product ID {self.product_id} by User ID {self.user_id}>'

# Function to initialize the database (and create tables)
def init_db(app):
    with app.app_context():
        db.create_all()
