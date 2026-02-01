from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this'  # Required for session management

# --- LOGIN SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- MOCK DATABASE ---
# Pre-seeding your account. Password is 'password123'
users_db = {
    'armasupplyguy@gmail.com': {
        'password': generate_password_hash('password123'),
        'name': 'Arma Guy'
    },
    'staff@example.com': {
        'password': generate_password_hash('password123'),
        'name': 'Regular Staff'
    }
}

# --- USER CLASS ---
class User(UserMixin):
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email
        
        # RULE: armasupplyguy@gmail.com automatically gets super admin. No matter what.
        if self.email == 'armasupplyguy@gmail.com':
            self.role = 'super_admin'
        else:
            self.role = 'staff'

@login_manager.user_loader
def load_user(user_id):
    if user_id in users_db:
        user_data = users_db[user_id]
        return User(user_id, user_data['name'], user_id)
    return None

# --- HTML TEMPLATE ---
page_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Staff Portal</title>
    <style>
        /* BASE STYLES */
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            box-sizing: border-box;
            background-color: #ecf0f1;
        }

        /* LOGIN PAGE STYLES */
        .login-container {
            width: 300px;
            margin: 100px auto;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .login-container input {
            width: 90%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .login-container button {
            width: 100%;
            padding: 10px;
            background-color: #2c3e50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .flash-msg { color: red; margin-bottom: 10px; }

        /* PORTAL STYLES (Only active when logged in) */
        {% if current_user.is_authenticated %}
        /* TOP MENU: Fixed at the top, spans full width */
        .top-menu {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 60px;
            background-color: #2c3e50; /* Dark Blue */
            color: white;
            display: flex;
            align-items: center;
            padding: 0 20px;
            z-index: 1000;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }

        .top-menu button {
            background-color: #34495e;
            color: white;
            border: 1px solid #7f8c8d;
            padding: 8px 15px;
            margin-right: 10px;
            cursor: pointer;
            border-radius: 4px;
        }
        
        .top-menu button:hover { background-color: #1abc9c; }
        .top-menu a { text-decoration: none; } /* For logout link */

        /* LEFT MENU: Fixed to the left, starts below top menu */
        .left-menu {
            position: fixed;
            top: 60px;
            left: 0;
            bottom: 0;
            width: 200px;
            background-color: #34495e;
            color: white;
            padding: 20px;
            overflow-y: auto;
            z-index: 900;
        }

        .left-menu button {
            display: block;
            width: 100%;
            background-color: transparent;
            color: white;
            border: none;
            text-align: left;
            padding: 15px 10px;
            cursor: pointer;
            border-bottom: 1px solid #7f8c8d;
        }

        .left-menu button:hover {
            background-color: #2c3e50;
            padding-left: 15px;
            transition: 0.2s;
        }

        /* MAIN CONTENT */
        .main-content {
            margin-top: 60px;
            margin-left: 200px;
            padding: 40px;
            min-height: 200vh;
        }
        {% endif %}
    </style>
</head>
<body>

    {% if current_user.is_authenticated %}
        <div class="top-menu">
            <h3 style="margin-right: 30px;">STAFF PORTAL</h3>
            <button>Dashboard</button>
            <button>Notifications</button>
            <button>Profile</button>
            <button>Settings</button>
            
            <div style="margin-left: auto; display: flex; align-items: center;">
                <span style="margin-right: 15px; font-size: 0.9em;">
                    {{ current_user.email }} <br> 
                    <small>({{ current_user.role }})</small>
                </span>
                <a href="{{ url_for('logout') }}"><button style="background-color: #c0392b; border-color: #e74c3c;">Logout</button></a>
            </div>
        </div>

        <div class="left-menu">
            <button>Employee List</button>
            <button>Time Off Requests</button>
            <button>Payroll</button>
            <button>Performance Reviews</button>
            <button>Recruitment</button>
        </div>

        <div class="main-content">
            <h1>Welcome, {{ current_user.name }}</h1>
            <p>You are logged in as: <strong>{{ current_user.role }}</strong></p>
            <hr>
            <p>Scroll down to test the fixed menus.</p>
            <br>
            <p>Content Line 1</p>
            <br><br><br><br><br>
            <p>Content Line 2</p>
            <br><br><br><br><br>
            <p>Content Line 3</p>
            <br><br><br><br><br>
            <p>Content Line 4</p>
            <br><br><br><br><br>
            <p>Content Line 5</p>
            <br><br><br><br><br>
            <p>Content Line 6</p>
            <br><br><br><br><br>
            <p>End of Content</p>
        </div>

    {% else %}
        <div class="login-container">
            <h2>Staff Login</h2>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="flash-msg">{{ messages[0] }}</div>
                {% endif %}
            {% endwith %}
            <form method="POST" action="/login">
                <input type="email" name="email" placeholder="Email" required value="armasupplyguy@gmail.com">
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <p style="font-size: 12px; color: #7f8c8d; margin-top: 10px;">Default password is: <b>password123</b></p>
        </div>
    {% endif %}

</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
@login_required
def home():
    return render_template_string(page_template)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in users_db:
            user_data = users_db[email]
            if check_password_hash(user_data['password'], password):
                user = User(email, user_data['name'], email)
                login_user(user)
                return redirect(url_for('home'))
        
        flash('Invalid email or password')
    return render_template_string(page_template)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
