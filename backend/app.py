from flask import Flask, render_template, redirect, url_for, request, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)
app.secret_key = '2163'

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Crear un modelo de usuario
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Configuración de la conexión a la base de datos MySQL
config = {
    'user': 'root',
    'password': '2163',
    'host': '127.0.0.1',
    'database': 'tienda_apc'
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Conectar a la base de datos
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()
        cursor.execute('SELECT id, password FROM usuarios WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        cnx.close()

        if user and check_password_hash(user[1], password):
            user_id = user[0]
            login_user(User(user_id))
            return redirect(url_for('profile'))

        return 'Login failed'

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user_id=current_user.id)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()
        try:
            cursor.execute('INSERT INTO usuarios (username, password) VALUES (%s, %s)', (username, hashed_password))
            cnx.commit()
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            cnx.rollback()
            return f"Error: {err}", 500
        finally:
            cursor.close()
            cnx.close()

    return render_template('register.html')

@app.route('/productos')
def productos():
    try:
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor(dictionary=True)
        cursor.execute('SELECT * FROM productos')
        productos = cursor.fetchall()
        cursor.close()
        cnx.close()
        return render_template('productos.html', productos=productos)
    except mysql.connector.Error as err:
        return f"Error: {err}", 500

@app.route('/producto/<int:producto_id>')
def obtener_producto(producto_id):
    try:
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor(dictionary=True)
        cursor.execute('SELECT * FROM productos WHERE id = %s', (producto_id,))
        producto = cursor.fetchone()
        cursor.close()
        cnx.close()
        if producto:
            return render_template('producto.html', producto=producto)
        else:
            return "Producto no encontrado", 404
    except mysql.connector.Error as err:
        return f"Error: {err}", 500

@app.route('/add_to_cart/<int:producto_id>', methods=['POST'])
def add_to_cart(producto_id):
    if 'cart' not in session:
        session['cart'] = {}

    cantidad = request.form.get('cantidad', 1, type=int)
    producto_id_str = str(producto_id)  # Convertir a cadena
    if producto_id_str in session['cart']:
        session['cart'][producto_id_str] += cantidad
    else:
        session['cart'][producto_id_str] = cantidad

    session.modified = True  # Asegúrate de que la sesión se modifique
    print(f"Producto con ID: {producto_id_str} añadido al carrito con cantidad: {session['cart'][producto_id_str]}")
    return redirect(url_for('carrito'))

@app.route('/carrito')
def carrito():
    # Inicializa las variables para manejar el carrito vacío
    productos_con_cantidades = []
    total = 0

    if 'cart' not in session or not session['cart']:
        session['cart'] = {}
    else:
        cart = session['cart']

        # Conectar a la base de datos y obtener los productos
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        producto_ids = list(cart.keys())

        if producto_ids:
            cursor.execute('SELECT * FROM productos WHERE id IN (%s)' % ','.join(['%s'] * len(producto_ids)), producto_ids)
            productos = cursor.fetchall()

            for producto in productos:
                producto_id = producto['id']
                cantidad = cart.get(str(producto_id), 0)
                subtotal = producto['precio'] * cantidad
                total += subtotal
                productos_con_cantidades.append({**producto, 'cantidad': cantidad, 'subtotal': subtotal})

        conn.close()

    return render_template('carrito.html', productos=productos_con_cantidades, total=total)

@app.route('/remove_from_cart/<int:producto_id>', methods=['POST'])
def remove_from_cart(producto_id):
    print(f"Intentando eliminar el producto con ID: {producto_id}")
    if 'cart' in session and str(producto_id) in session['cart']:
        del session['cart'][str(producto_id)]
        session.modified = True
        print(f"Producto con ID: {producto_id} eliminado del carrito.")
    else:
        print(f"Producto con ID: {producto_id} no encontrado en el carrito.")
    return redirect(url_for('carrito'))

def get_db_connection():
    connection = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='2163',
        database='tienda_apc'
    )
    return connection

if __name__ == '__main__':
    app.run(debug=True)