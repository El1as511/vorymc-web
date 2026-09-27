import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'vorymc_llave_secreta_super_segura_2026'
DB_NAME = "vorymc_staff.db"

# --- CONFIGURACIÓN DE BASE DE DATOS ---
def init_db():
    """Crea la tabla de staff si no existe."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rango TEXT DEFAULT 'Staff'
        )
    ''')
    conn.commit()
    conn.close()

def crear_usuario_console(username, password, rango="Staff"):
    """Función para crear usuarios manualmente desde la consola."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Guardamos la contraseña encriptada por seguridad
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO staff (username, password, rango) VALUES (?, ?, ?)", 
                       (username, hashed_password, rango))
        conn.commit()
        print(f"✅ ¡Usuario '{username}' ({rango}) creado con éxito en la base de datos!")
    except sqlite3.IntegrityError:
        print(f"❌ Error: El usuario '{username}' ya existe.")
    finally:
        conn.close()

# Inicializamos la base de datos al arrancar
init_db()


# --- RUTAS DE LA APLICACIÓN ---

# 1. Página principal pública ( / )
@app.route('/')
def home():
    return render_template('index.html')


# 2. Login de Staff ( /login )
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('is_staff'):
        return redirect(url_for('staff_main'))

    error = None
    if request.method == 'POST':
        username_input = request.form.get('username').strip()
        password_input = request.form.get('password')

        # Buscar usuario en la base de datos
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password, rango FROM staff WHERE LOWER(username) = LOWER(?)", (username_input,))
        user_data = cursor.fetchone()
        conn.close()

        # Verificar credenciales
        if user_data and check_password_hash(user_data[0], password_input):
            session['is_staff'] = True
            session['username'] = username_input
            session['rango'] = user_data[1]
            return redirect(url_for('staff_main'))
        else:
            error = "Usuario o contraseña incorrectos."

    return render_template('login.html', error=error)


# 3. Página Principal del Staff ( /staff )
@app.route('/staff')
def staff_main():
    # Proteger la ruta: si no hay sesión activa, manda al login
    if not session.get('is_staff'):
        return redirect(url_for('login'))
    
    return render_template('staff_main.html', 
                           username=session.get('username'), 
                           rango=session.get('rango'))


# 4. Cerrar Sesión ( /logout )
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)

def eliminar_usuario_console(username):
    """Función para eliminar un usuario de staff por su nickname desde la consola."""
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Verificar si el usuario existe antes de borrarlo
    cursor.execute("SELECT id FROM staff WHERE LOWER(username) = LOWER(?)", (username.strip(),))
    existe = cursor.fetchone()
    
    if existe:
        cursor.execute("DELETE FROM staff WHERE LOWER(username) = LOWER(?)", (username.strip(),))
        conn.commit()
        print(f"🗑️ ¡Usuario '{username}' eliminado con éxito de la base de datos!")
    else:
        print(f"❌ Error: El usuario '{username}' no existe en la base de datos.")
        
    conn.close()