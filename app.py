from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
# Clave secreta (en producción cámbiala por una muy segura)
app.secret_key = 'velvetpages_secret_key_12345'

# Base de datos local (SQLite). Se creará un archivo llamado velvetpages.db en tu PC.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///velvetpages.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE BASE DE DATOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_premium = db.Column(db.Boolean, default=True) # Simulando que ya pagaron
    libros = db.relationship('Book', backref='owner', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(200))
    imagen = db.Column(db.Text) # Imagen en Base64
    estrellas = db.Column(db.Float, default=0.0)
    paginas = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --- RUTAS DE LA WEB ---
@app.route('/')
def index():
    # Muestra el archivo templates/index.html
    return render_template('index.html')

# --- API DE AUTENTICACIÓN ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "El correo ya está registrado"}), 400
        
    hashed_password = generate_password_hash(password)
    nuevo_usuario = User(email=email, password_hash=hashed_password)
    db.session.add(nuevo_usuario)
    db.session.commit()
    
    session['user_id'] = nuevo_usuario.id
    return jsonify({"mensaje": "Registro exitoso"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        return jsonify({"mensaje": "Login exitoso"}), 200
        
    return jsonify({"error": "Credenciales incorrectas"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"mensaje": "Sesión cerrada"}), 200

# --- API DE LIBROS ---
@app.route('/api/libros', methods=['GET'])
def get_libros():
    if 'user_id' not in session: return jsonify({"error": "No autorizado"}), 401
    user = User.query.get(session['user_id'])
    libros = [{"id": l.id, "titulo": l.titulo, "autor": l.autor, "imagen": l.imagen, "estrellas": l.estrellas, "paginas": l.paginas} for l in user.libros]
    return jsonify(libros)

@app.route('/api/libros', methods=['POST'])
def add_libro():
    if 'user_id' not in session: return jsonify({"error": "No autorizado"}), 401
    data = request.json
    nuevo_libro = Book(
        titulo=data['titulo'], autor=data['autor'], 
        imagen=data['imagen'], estrellas=data['estrellas'], paginas=data['paginas'],
        user_id=session['user_id']
    )
    db.session.add(nuevo_libro)
    db.session.commit()
    return jsonify({"mensaje": "Libro guardado"}), 201

@app.route('/api/libros/<int:id>', methods=['DELETE'])
def delete_libro(id):
    if 'user_id' not in session: return jsonify({"error": "No autorizado"}), 401
    libro = Book.query.filter_by(id=id, user_id=session['user_id']).first()
    if libro:
        db.session.delete(libro)
        db.session.commit()
        return jsonify({"mensaje": "Libro eliminado"})
    return jsonify({"error": "No encontrado"}), 404

# --- INICIO DE LA APP ---
if __name__ == '__main__':
    # Crea las tablas de la base de datos si no existen
    with app.app_context():
        db.create_all()
    
    # Ejecuta el servidor local en el puerto 5000
    app.run(debug=True)