import pytest
from app import app, User, bcrypt

# Crear un cliente de prueba
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Usar una base de datos en memoria
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    with app.test_client() as client:
        with app.app_context():
            from app import db  # Mover la importación aquí para evitar la duplicación de la instancia
            db.create_all()  # Crear las tablas dentro del contexto de la aplicación
        yield client
        with app.app_context():
            from app import db  # Asegurarse de que la importación de db sea dentro del contexto
            db.drop_all()  # Eliminar las tablas después de cada prueba

# Test de inicio de sesión exitoso
def test_login_success(client):
    # Primero, registramos un usuario con contraseña hasheada
    password_hash = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    with app.app_context():
        user = User(name='Carlos', surnames='Perez', email='carlos@example.com', password=password_hash)
        from app import db
        db.session.add(user)
        db.session.commit()

    # Intentamos hacer login con las credenciales correctas
    response = client.post('/login', data={
        'email': 'carlos@example.com',
        'password': 'password123'
    })

    assert response.status_code == 302  # Redirección después de un login exitoso
    assert response.headers['Location'] == '/tasks'  # Redirección a la página de tareas

# Test de inicio de sesión con contraseña incorrecta
def test_login_incorrect_password(client):
    # Primero, registramos un usuario con contraseña hasheada
    password_hash = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    with app.app_context():
        user = User(name='Carlos', surnames='Perez', email='carlos@example.com', password=password_hash)
        from app import db
        db.session.add(user)
        db.session.commit()

    # Intentamos hacer login con una contraseña incorrecta
    response = client.post('/login', data={
        'email': 'carlos@example.com',
        'password': 'wrongpassword'
    })

    assert response.status_code == 200  # La respuesta debe ser 200 (sin redirección)
    assert b'Las credenciales no son correctas' in response.data  # Verificar el mensaje de error

# Test de inicio de sesión con usuario no registrado
def test_login_user_not_found(client):
    # Intentamos hacer login con un usuario que no existe
    response = client.post('/login', data={
        'email': 'nonexistent@example.com',
        'password': 'anyPassword'
    })

    assert response.status_code == 200  # La respuesta debe ser 200 (sin redirección)
    assert b'Las credenciales no son correctas' in response.data  # Verificar el mensaje de error

# Test de inicio de sesión con campos vacíos
def test_login_empty_fields(client):
    # Intentamos hacer login con campos vacíos
    response = client.post('/login', data={
        'email': '',
        'password': ''
    })

    assert response.status_code == 200  # La respuesta debe ser 200 (sin redirección)
    # Inspecciona la respuesta HTML y verifica el texto correcto
    assert b'Este campo es obligatorio' in response.data  # Ajusta esto según el mensaje real de error

# Test de inicio de sesión con formato de correo electrónico incorrecto
def test_login_invalid_email_format(client):
    # Intentamos hacer login con un formato de correo electrónico inválido
    response = client.post('/login', data={
        'email': 'invalidemail.com',
        'password': 'password123'
    })

    assert response.status_code == 200  # La respuesta debe ser 200 (sin redirección)
    # Convertir response.data a cadena para comparar
    assert 'El formato del correo electrónico es inválido' in response.data.decode('utf-8')  # Verificar mensaje de error


# Test de redirección a la página de login si no hay sesión activa
def test_redirect_to_login_if_not_authenticated(client):
    # Intentamos acceder a una página protegida sin estar autenticado
    response = client.get('/tasks')  # Suponiendo que '/tasks' es una página protegida

    assert response.status_code == 302  # Redirección
    assert response.headers['Location'] == '/'  # Verificar que redirige a '/login'
