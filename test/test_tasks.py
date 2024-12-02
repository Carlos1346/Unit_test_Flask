import pytest
from app import app, db, Task
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

# Test de acceso a /tasks sin estar autenticado
def test_tasks_without_token(client):
    response = client.get('/tasks')
    assert response.status_code == 302  # Redirección a la página de inicio
    assert b'Redirecting' in response.data  # Confirmar que se está redirigiendo
    assert response.headers['Location'] == '/'  # Verificar la URL de redirección

# Test de acceso a /tasks con un token de sesión válido
def test_tasks_with_token(client):
    # Crear un usuario ficticio
    email = 'test@example.com'
    task = Task(email=email, title='Test Task', description='Test description', date_task='2024-12-01')
    
    with app.app_context():
        db.session.add(task)
        db.session.commit()
    
    # Simular un usuario autenticado
    with client.session_transaction() as sess:
        sess['token'] = 'valid_token'
        sess['email'] = email  # Establecer el email en la sesión
    
    # Hacer la solicitud GET a /tasks
    response = client.get('/tasks')
    
    assert response.status_code == 200  # Respuesta correcta
    assert b'Test Task' in response.data  # Verificar que la tarea esté en la respuesta
    assert b'Test description' in response.data  # Verificar que la descripción de la tarea esté en la respuesta

# Test de acceso a /tasks con un token válido pero sin tareas asociadas
def test_tasks_with_token_no_tasks(client):
    # Crear un usuario ficticio sin tareas
    email = 'test@example.com'
    
    # Simular un usuario autenticado
    with client.session_transaction() as sess:
        sess['token'] = 'valid_token'
        sess['email'] = email  # Establecer el email en la sesión
    
    # Hacer la solicitud GET a /tasks
    response = client.get('/tasks')
    
    assert response.status_code == 200  # Respuesta correcta
    assert b'No tasks available' in response.data  # Verificar que no haya tareas disponibles

# Test de tarea con múltiples elementos en la base de datos
def test_tasks_with_multiple_tasks(client):
    # Crear un usuario ficticio
    email = 'test@example.com'
    tasks = [
        Task(email=email, title='Task 1', description='Description 1', date_task='2024-12-01'),
        Task(email=email, title='Task 2', description='Description 2', date_task='2024-12-02'),
        Task(email=email, title='Task 3', description='Description 3', date_task='2024-12-03')
    ]
    
    with app.app_context():
        db.session.add_all(tasks)
        db.session.commit()
    
    # Simular un usuario autenticado
    with client.session_transaction() as sess:
        sess['token'] = 'valid_token'
        sess['email'] = email  # Establecer el email en la sesión
    
    # Hacer la solicitud GET a /tasks
    response = client.get('/tasks')
    
    assert response.status_code == 200  # Respuesta correcta
    assert b'Task 1' in response.data  # Verificar que la tarea 1 esté en la respuesta
    assert b'Task 2' in response.data  # Verificar que la tarea 2 esté en la respuesta
    assert b'Task 3' in response.data  # Verificar que la tarea 3 esté en la respuesta

