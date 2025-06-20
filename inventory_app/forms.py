from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .models import User # Corrected: Relative import

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email',
                        validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    # Role selection could be added here if admins can create other admins,
    # or if users can choose a role (less common for this field).
    # For now, new users are 'user' role by default as per model.
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use. Please choose a different one.')

class LoginForm(FlaskForm):
    # Can use email or username to login
    email_or_username = StringField('Email or Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = StringField('Description', validators=[Length(max=500)]) # Using StringField for simple textarea
    quantity = StringField('Quantity', validators=[DataRequired()]) # Use StringField to accept 0, then convert
    price = StringField('Price', validators=[DataRequired()]) # Use StringField, then convert
    sku = StringField('SKU (Stock Keeping Unit)', validators=[Length(max=50)])
    category = StringField('Category', validators=[Length(max=100)])
    supplier = StringField('Supplier', validators=[Length(max=100)])
    submit = SubmitField('Save Product')

    def validate_quantity(self, quantity):
        try:
            val = int(quantity.data)
            if val < 0:
                raise ValidationError('Quantity cannot be negative.')
        except ValueError:
            raise ValidationError('Invalid quantity. Must be a whole number.')

    def validate_price(self, price):
        try:
            val = float(price.data)
            if val < 0:
                raise ValidationError('Price cannot be negative.')
        except ValueError:
            raise ValidationError('Invalid price. Must be a number.')

class StockAdjustmentForm(FlaskForm):
    quantity_change = StringField('Quantity Change', validators=[DataRequired()])
    movement_type = SelectField('Movement Type', choices=[
        ('stock_entry', 'Stock Entry (Receiving)'),
        ('sale', 'Sale'),
        ('return', 'Customer Return'),
        ('damage_loss', 'Damage / Loss'),
        ('adjustment_manual', 'Manual Adjustment')
        # More types can be added as needed
    ], validators=[DataRequired()])
    notes = StringField('Notes/Reference ID (e.g., Order #, Reason)', validators=[Length(max=500)])
    submit = SubmitField('Adjust Stock')

    def validate_quantity_change(self, quantity_change):
        try:
            val = int(quantity_change.data)
            # For this form, quantity_change is the amount to add or remove.
            # The sign will be determined by the context (add_stock vs remove_stock) or selected type.
            # For now, let's assume it's always positive from the form, and logic handles +/-.
            # Or, we can allow negative numbers for direct adjustments.
            # For simplicity here, let's assume it's the magnitude of change.
            if val == 0: # Or val <= 0 if we expect it to be always positive for "change"
                 raise ValidationError('Quantity change cannot be zero.')
        except ValueError:
            raise ValidationError('Invalid quantity. Must be a whole number.')

class AddStockForm(FlaskForm):
    quantity_added = StringField('Quantity to Add', validators=[DataRequired()])
    notes = StringField('Notes/Reference ID (e.g., Shipment #, PO #)', validators=[Length(max=255)])
    submit = SubmitField('Add Stock')

    def validate_quantity_added(self, quantity_added):
        try:
            val = int(quantity_added.data)
            if val <= 0:
                raise ValidationError('Quantity to add must be a positive number.')
        except ValueError:
            raise ValidationError('Invalid quantity. Must be a whole number.')

class RemoveStockForm(FlaskForm):
    quantity_removed = StringField('Quantity to Remove', validators=[DataRequired()])
    reason = SelectField('Reason', choices=[
        ('sale', 'Sale'),
        ('damage', 'Damaged Goods'),
        ('loss', 'Lost/Stolen'),
        ('internal_use', 'Internal Use'),
        ('adjustment_out', 'Manual Adjustment Out')
    ], validators=[DataRequired()])
    notes = StringField('Notes/Reference ID (e.g., Order #, Incident Report #)', validators=[Length(max=255)])
    submit = SubmitField('Remove Stock')

    def validate_quantity_removed(self, quantity_removed):
        try:
            val = int(quantity_removed.data)
            if val <= 0:
                raise ValidationError('Quantity to remove must be a positive number.')
        except ValueError:
            raise ValidationError('Invalid quantity. Must be a whole number.')
