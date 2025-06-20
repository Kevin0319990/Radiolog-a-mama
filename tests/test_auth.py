from tests.base import BaseTestCase
from inventory_app.models import User, db
from flask import get_flashed_messages, url_for # Added url_for

class TestAuth(BaseTestCase):

    def test_user_registration(self):
        response = self.register_user(username="newuser", email="new@example.com", password="password123")
        self.assertEqual(response.status_code, 200) # Assuming redirect to login, which is 200

        # Check user in database
        user = User.query.filter_by(email="new@example.com").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "newuser")
        self.assertTrue(user.check_password("password123"))

        # Check flash message
        # To check flashed messages, you need to access them from the response context or session
        # This is a bit more complex with test_client if redirects are followed.
        # A simpler way is to check for text on the page if the flash message is rendered.
        self.assertIn(b'Your account has been created!', response.data)


    def test_duplicate_username_registration(self):
        self.register_user(username="dupuser", email="dup1@example.com", password="password")
        response = self.register_user(username="dupuser", email="dup2@example.com", password="password")
        self.assertEqual(response.status_code, 200) # Stays on registration page
        self.assertIn(b'That username is already taken.', response.data)
        user_count = User.query.filter_by(username="dupuser").count()
        self.assertEqual(user_count, 1)

    def test_duplicate_email_registration(self):
        self.register_user(username="emailuser1", email="duplicate@example.com", password="password")
        response = self.register_user(username="emailuser2", email="duplicate@example.com", password="password")
        self.assertEqual(response.status_code, 200) # Stays on registration page
        self.assertIn(b'That email is already in use.', response.data)
        user_count = User.query.filter_by(email="duplicate@example.com").count()
        self.assertEqual(user_count, 1)

    def test_successful_login_logout_with_email(self):
        self.register_user(username="loginuser", email="login@example.com", password="securepassword")

        # Logout if testuser is somehow logged in from previous tests (though setUp should handle this)
        self.logout_user()

        login_response = self.login_user(email_or_username="login@example.com", password="securepassword")
        self.assertEqual(login_response.status_code, 200) # Redirect to index
        self.assertIn(b'Login successful!', login_response.data) # Check flash message

        # Check correct nav links are present/absent
        decoded_data = login_response.data.decode('utf-8')
        # Check for relative paths as rendered in HTML
        self.assertIn('href="/logout"', decoded_data) # Or url_for('main.logout', _external=False)
        self.assertNotIn('href="/login"', decoded_data)

        # Test accessing a protected page
        products_response = self.client.get(url_for('main.products'))
        self.assertEqual(products_response.status_code, 200) # Should be accessible
        self.assertIn('Gestión de Productos', products_response.data.decode('utf-8'))

        logout_response = self.logout_user()
        self.assertEqual(logout_response.status_code, 200) # Redirect to login
        self.assertIn(b'You have been logged out.', logout_response.data)

        decoded_logout_data = logout_response.data.decode('utf-8')
        self.assertIn('href="/login"', decoded_logout_data) # Login link href should be visible again
        self.assertNotIn('href="/logout"', decoded_logout_data) # Logout link href should NOT be visible

        # Test accessing a protected page after logout
        products_response_after_logout = self.client.get(url_for('main.products'), follow_redirects=True)
        self.assertEqual(products_response_after_logout.status_code, 200) # Redirects to login
        self.assertIn(b'Please log in to access this page', products_response_after_logout.data) # Flash message from Flask-Login

    def test_successful_login_with_username(self):
        self.register_user(username="loginuser_un", email="login_un@example.com", password="securepassword")
        self.logout_user()

        login_response = self.login_user(email_or_username="loginuser_un", password="securepassword")
        self.assertEqual(login_response.status_code, 200)
        self.assertIn(b'Login successful!', login_response.data)

    def test_unsuccessful_login_wrong_password(self):
        self.register_user(email="wrongpass@example.com", password="correctpassword")
        self.logout_user()

        response = self.login_user(email_or_username="wrongpass@example.com", password="incorrectpassword")
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Login Unsuccessful.', response.data)
        self.assertIn(b'Login', response.data) # Login link still there
        self.assertNotIn(b'Logout', response.data)

    def test_unsuccessful_login_nonexistent_user(self):
        response = self.login_user(email_or_username="nouser@example.com", password="anypassword")
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Login Unsuccessful.', response.data)

    def test_access_protected_route_unauthenticated(self):
        response = self.client.get('/products', follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirects to login
        self.assertIn(b'Please log in to access this page', response.data) # Default Flask-Login message
        self.assertIn('Iniciar Sesión', response.data.decode('utf-8')) # Login page title

if __name__ == '__main__':
    unittest.main()
