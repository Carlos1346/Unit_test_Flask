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
            db.create_all()  # Crear las tablas dentro del contexto de la aplicación
        yield client
        with app.app_context():
            db.drop_all()  # Eliminar las tablas después de cada prueba


# Test de intento de eliminación de un proyecto que no existe
def test_delete_project_not_found(client):
    # Simular un usuario autenticado dentro del contexto de la aplicación
    with client.session_transaction() as sess:
        sess['token'] = 'valid_token'
        sess['email'] = 'test@example.com'  # Establecer el email en la sesión
    
    # Intentar eliminar un proyecto que no existe
    response = client.post('/delete-project', data={'id': 9999})  # ID de un proyecto que no existe
    
    # Verificar que la respuesta sea una redirección a la página de proyectos
    assert response.status_code == 302
    assert response.headers['Location'] == '/projects'


# Test de eliminación de proyecto con un ID no válido sin estar autenticado
def test_delete_project_invalid_id_without_token(client):
    # Intentar eliminar un proyecto con un ID no válido sin estar autenticado
    response = client.post('/delete-project', data={'id': 'invalid_id'})
    
    # Verificar que la respuesta sea una redirección a la página de inicio (home) porque no hay token
    assert response.status_code == 302
    assert response.headers['Location'] == '/'  # Redirige a la página de inicio


# Test de eliminación de proyecto con token válido pero con ID no válido
def test_delete_project_invalid_id_with_token(client):
    # Crear un proyecto ficticio dentro del contexto de la aplicación
    with app.app_context():
        project = Project(user_email='test@example.com', title='Test Project', description='Test description', start_date='2024-12-01', end_date='2024-12-31')
        db.session.add(project)
        db.session.commit()

    # Simular un usuario autenticado dentro del contexto de la aplicación
    with client.session_transaction() as sess:
        sess['token'] = 'valid_token'
        sess['email'] = 'test@example.com'  # Establecer el email en la sesión

    # Intentar eliminar un proyecto con un ID no válido (tipo de dato incorrecto)
    response = client.post('/delete-project', data={'id': 'invalid_id'})
    
    # Verificar que la respuesta sea una redirección a la página de proyectos
    assert response.status_code == 302
    assert response.headers['Location'] == '/projects'  # Redirige a la lista de proyectos

