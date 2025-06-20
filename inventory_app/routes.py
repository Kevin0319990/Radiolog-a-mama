from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps # For admin_required

# Import db instance and models from .models
# The db instance is initialized in __init__.py's create_app
from . import db # Import db from __init__.py of the current package
from .models import User, Product, InventoryMovement

# Import forms
from .forms import LoginForm, RegistrationForm, ProductForm, AddStockForm, RemoveStockForm

main = Blueprint('main', __name__)

# User loader for Flask-Login - needs to be associated with login_manager
# login_manager is in __init__.py. This is tricky.
# Usually, login_manager.user_loader is defined where login_manager is instantiated or after app context.
# For now, let's assume login_manager is accessible or this needs to be called from create_app.
# This will be handled in __init__.py's create_app after User model is available.

# Custom decorator for admin required
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('main.index')) # Blueprint routes are prefixed
        return f(*args, **kwargs)
    return decorated_function

# Routes (copied from app.py and adapted for Blueprint 'main')

@main.route('/')
def index():
    return render_template('index.html', footer_text="Elaborado por Kevin Castellanos")

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form, footer_text="Elaborado por Kevin Castellanos")

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.email == form.email_or_username.data) | (User.username == form.email_or_username.data)).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            # Ensure next_page is safe before redirecting
            # if next_page and not is_safe_url(next_page): # is_safe_url needs to be defined
            # return redirect(url_for('main.index'))
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Login Unsuccessful. Please check email/username and password.', 'danger')
    return render_template('login.html', title='Login', form=form, footer_text="Elaborado por Kevin Castellanos")

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main.route('/products')
@login_required
def products():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
    products_query = Product.query.order_by(Product.name)
    paginated_products = products_query.paginate(page=page, per_page=per_page, error_out=False)
    total_unique_products = products_query.count()
    total_units_in_inventory = db.session.query(db.func.sum(Product.quantity)).scalar() or 0
    low_stock_threshold = current_app.config.get('LOW_STOCK_THRESHOLD', 10)
    return render_template('products.html',
                           products=paginated_products,
                           total_unique_products=total_unique_products,
                           total_units_in_inventory=total_units_in_inventory,
                           low_stock_threshold=low_stock_threshold,
                           footer_text="Elaborado por Kevin Castellanos")

@main.route('/product/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        existing_product_name = Product.query.filter_by(name=form.name.data).first()
        if existing_product_name:
            flash('Product name already exists.', 'danger')
            return render_template('product_form.html', title='Add New Product', form=form, footer_text="Elaborado por Kevin Castellanos")
        if form.sku.data:
            existing_product_sku = Product.query.filter_by(sku=form.sku.data).first()
            if existing_product_sku:
                flash('Product SKU already exists.', 'danger')
                return render_template('product_form.html', title='Add New Product', form=form, footer_text="Elaborado por Kevin Castellanos")
        product = Product(
            name=form.name.data, description=form.description.data,
            quantity=int(form.quantity.data), price=float(form.price.data),
            sku=form.sku.data if form.sku.data else None,
            category=form.category.data, supplier=form.supplier.data
        )
        db.session.add(product)
        db.session.commit()
        if product.quantity > 0:
            initial_movement = InventoryMovement(
                product_id=product.id, user_id=current_user.id,
                quantity_change=product.quantity, movement_type='initial_stock',
                notes='Product created with initial stock.'
            )
            db.session.add(initial_movement)
            db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('main.products'))
    return render_template('product_form.html', title='Add New Product', form=form, footer_text="Elaborado por Kevin Castellanos")

@main.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        if product.name != form.name.data:
            existing_product_name = Product.query.filter_by(name=form.name.data).first()
            if existing_product_name:
                flash('Product name already exists.', 'danger')
                return render_template('product_form.html', title='Edit Product', form=form, product=product, footer_text="Elaborado por Kevin Castellanos")
        if form.sku.data and product.sku != form.sku.data:
            existing_product_sku = Product.query.filter_by(sku=form.sku.data).first()
            if existing_product_sku:
                flash('Product SKU already exists.', 'danger')
                return render_template('product_form.html', title='Edit Product', form=form, product=product, footer_text="Elaborado por Kevin Castellanos")

        original_quantity = product.quantity
        new_quantity = int(form.quantity.data)
        product.name = form.name.data
        product.description = form.description.data
        product.quantity = new_quantity
        product.price = float(form.price.data)
        product.sku = form.sku.data if form.sku.data else None
        product.category = form.category.data
        product.supplier = form.supplier.data
        product.last_updated = db.func.now()

        if original_quantity != new_quantity:
            movement = InventoryMovement(
                product_id=product.id, user_id=current_user.id,
                quantity_change=new_quantity - original_quantity,
                movement_type='adjustment_edit',
                notes=f"Product details edited. Quantity changed from {original_quantity} to {new_quantity}."
            )
            db.session.add(movement)
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('main.products'))
    return render_template('product_form.html', title='Edit Product', form=form, product=product, footer_text="Elaborado por Kevin Castellanos")

@main.route('/product/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Consider soft delete or checks for related movements later
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('main.products'))

@main.route('/product/<int:product_id>/add_stock', methods=['GET', 'POST'])
@admin_required
def add_stock(product_id):
    product = Product.query.get_or_404(product_id)
    form = AddStockForm()
    if form.validate_on_submit():
        quantity_added = int(form.quantity_added.data)
        product.quantity += quantity_added
        product.last_updated = db.func.now()
        movement = InventoryMovement(
            product_id=product.id, user_id=current_user.id,
            quantity_change=quantity_added, movement_type='stock_entry',
            notes=form.notes.data
        )
        db.session.add(movement)
        db.session.commit()
        flash(f'{quantity_added} units of {product.name} added to stock.', 'success')
        return redirect(url_for('main.products'))
    return render_template('stock_adjustment_form.html', title=f'Add Stock for {product.name}', form=form, product=product, footer_text="Elaborado por Kevin Castellanos")

@main.route('/product/<int:product_id>/remove_stock', methods=['GET', 'POST'])
@admin_required
def remove_stock(product_id):
    product = Product.query.get_or_404(product_id)
    form = RemoveStockForm()
    if form.validate_on_submit():
        quantity_removed = int(form.quantity_removed.data)
        if quantity_removed > product.quantity:
            flash(f'Cannot remove {quantity_removed} units. Only {product.quantity} available.', 'danger')
            return render_template('stock_adjustment_form.html', title=f'Remove Stock for {product.name}', form=form, product=product, footer_text="Elaborado por Kevin Castellanos")
        product.quantity -= quantity_removed
        product.last_updated = db.func.now()
        movement = InventoryMovement(
            product_id=product.id, user_id=current_user.id,
            quantity_change=-quantity_removed, movement_type=form.reason.data,
            notes=form.notes.data
        )
        db.session.add(movement)
        db.session.commit()
        flash(f'{quantity_removed} units of {product.name} removed from stock.', 'success')
        return redirect(url_for('main.products'))
    return render_template('stock_adjustment_form.html', title=f'Remove Stock for {product.name}', form=form, product=product, footer_text="Elaborado por Kevin Castellanos")

@main.route('/reports')
@login_required
def reports_index():
    return render_template('reports_index.html', footer_text="Elaborado por Kevin Castellanos")

@main.route('/reports/low_stock')
@login_required
def low_stock_report():
    low_stock_threshold = current_app.config.get('LOW_STOCK_THRESHOLD', 10)
    low_stock_products = Product.query.filter(Product.quantity <= low_stock_threshold)\
                                      .order_by(Product.quantity.asc(), Product.name.asc()).all()
    return render_template('low_stock_report.html',
                           products=low_stock_products,
                           low_stock_threshold=low_stock_threshold,
                           title="Reporte de Productos con Bajo Stock",
                           footer_text="Elaborado por Kevin Castellanos")

@main.route('/reports/inventory_movements')
@login_required
def inventory_movements_report():
    # Placeholder: Add pagination and filtering later
    movements = InventoryMovement.query.order_by(InventoryMovement.timestamp.desc()).limit(20).all()
    return render_template('inventory_movements_report.html',
                           movements=movements,
                           title="Reporte de Movimientos de Inventario",
                           footer_text="Elaborado por Kevin Castellanos")

@main.route('/account')
@login_required
def account():
    # Placeholder for account page
    return render_template('index.html', title='My Account', footer_text="Elaborado por Kevin Castellanos")
