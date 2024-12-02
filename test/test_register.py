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

# Test de registro exitoso
def test_register_success(client):
    response = client.post('/register', data={
        'name': 'Carlos',
        'surnames': 'Perez',
        'email': 'carlos@example.com',
        'password': 'password123'
    })
    assert response.status_code == 302  # Redirección después de un registro exitoso
    assert response.headers['Location'] == '/'

    # Verificar si el usuario fue insertado en la base de datos
    from app import db  # Importar db dentro del contexto
    user = User.query.filter_by(email='carlos@example.com').first()
    assert user is not None
    assert user.name == 'Carlos'

# Test de registro con campos vacíos
def test_register_missing_fields(client):
    response = client.post('/register', data={
        'name': '',
        'surnames': '',
        'email': '',
        'password': ''
    })
    assert response.status_code == 200  # La respuesta debe ser 200
    assert b'Por favor, complete todos los campos.' in response.data  # Verificar mensaje de error

# Test de registro con un correo ya registrado
def test_register_existing_email(client):
    # Primero, registramos un usuario
    client.post('/register', data={
        'name': 'Carlos',
        'surnames': 'Perez',
        'email': 'carlos@example.com',
        'password': 'password123'
    })

    # Intentamos registrar otro usuario con el mismo correo
    response = client.post('/register', data={
        'name': 'Luis',
        'surnames': 'Gomez',
        'email': 'carlos@example.com',
        'password': 'password456'
    })
    assert response.status_code == 200
    assert 'El correo ya está registrado.' in response.get_data(as_text=True)
