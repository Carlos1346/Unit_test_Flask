import pytest
from app import app, db, Project
from flask import session

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

# Test de visualización de proyectos sin estar autenticado
def test_projects_without_token(client):
    # Crear un proyecto ficticio
    project = Project(user_email='test@example.com', title='Test Project', description='Test description', start_date='2024-12-01', end_date='2024-12-31')
    
    with app.app_context():
        db.session.add(project)
        db.session.commit()
    
    # Intentar acceder a la página de proyectos sin estar autenticado
    response = client.get('/projects')
    
    assert response.status_code == 302  # Redirección a la página de inicio
    assert response.headers['Location'] == '/'  # Verificar la URL de redirección

# Test de visualización de proyectos con token válido
def test_projects_with_token(client):
    # Crear un usuario ficticio y un proyecto
    email = 'test@example.com'
    project = Project(user_email=email, title='Test Project', description='Test description', start_date='2024-12-01', end_date='2024-12-31')
    
    with app.app_context():
        db.session.add(project)
        db.session.commit()
    
    # Simular un usuario autenticado
    with client.session_transaction() as sess:
        sess['token'] = 'valid_token'
        sess['email'] = email  # Establecer el email en la sesión
    
    # Acceder a la página de proyectos
    response = client.get('/projects')
    
    assert response.status_code == 200  # Debería cargar la página de proyectos correctamente
    assert b'Test Project' in response.data  # Verificar que el título del proyecto está en la respuesta

# Test de visualización de proyectos con token válido pero sin proyectos
def test_projects_with_token_no_projects(client):
    # Simular un usuario autenticado sin proyectos
    email = 'test@example.com'
    
    with client.session_transaction() as sess:
        sess['token'] = 'valid_token'
        sess['email'] = email  # Establecer el email en la sesión
    
    # Acceder a la página de proyectos cuando no hay proyectos
    response = client.get('/projects')
    
    assert response.status_code == 200  # Debería cargar la página de proyectos correctamente
    assert b'No tienes proyectos.' in response.data  # Verificar que el mensaje adecuado se muestra si no hay proyectos
