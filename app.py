from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt
import jwt
import config

app = Flask(__name__)
app.config.from_object(config.Config)


# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Definir los modelos de la base de datos
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surnames = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    date_task = db.Column(db.String(20), nullable=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    start_date = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20), nullable=False)

class ProjectComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    email = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)
    comment = db.Column(db.String(500), nullable=False)

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

# Ruta de login
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    # Verificar si el usuario existe
    user = User.query.filter_by(email=email).first()

    if user:
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):  # Verificación del hash
            # Generar token JWT
            token = jwt.encode({'email': email}, app.config['SECRET_KEY'], algorithm='HS256')
            # Guardar datos en la sesión
            session['token'] = token
            session['email'] = email
            session['name'] = user.name
            session['surnames'] = user.surnames

            return redirect(url_for('tasks'))
    return render_template('index.html', message="Las credenciales no son correctas")

# Ruta de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        surnames = request.form['surnames']
        email = request.form['email']
        password = request.form['password']

        # Verificar que todos los campos estén completos
        if not name or not surnames or not email or not password:
            return render_template('register.html', message="Por favor, complete todos los campos.")

        # Verificar que no exista el usuario
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return render_template('register.html', message="El correo ya está registrado.")
        
        # Hashear la contraseña
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # Asegurarse de que sea un string

        # Insertar nuevo usuario en la base de datos
        new_user = User(name=name, surnames=surnames, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('home'))  # Redirigir al home después de registrarse

    return render_template('register.html')

@app.route('/tasks', methods=['GET'])
def tasks():
    if 'token' not in session:
        return redirect(url_for('home'))
    
    email = session['email']
    tasks = Task.query.filter_by(email=email).all()

    tasks_list = []
    for task in tasks:
        tasks_list.append({
            'id': task.id,
            'email': task.email,
            'title': task.title,
            'description': task.description,
            'date_task': task.date_task
        })

    return render_template('tasks.html', tasks=tasks_list)

@app.route('/new-task', methods=['POST'])
def newTask():
    if 'token' not in session:
        return redirect(url_for('home'))

    title = request.form['title']
    description = request.form['description']
    email = session['email']
    d = datetime.now()
    dateTask = d.strftime("%Y-%m-%d %H:%M:%S")

    if title and description and email:
        new_task = Task(email=email, title=title, description=description, date_task=dateTask)
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('tasks'))

@app.route("/delete-task", methods=["POST"])
def deleteTask():
    if 'token' not in session:
        return redirect(url_for('home'))
    
    task_id = request.form['id']
    task = Task.query.filter_by(id=task_id).first()
    if task:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('tasks'))

# Nueva ruta para editar tarea
@app.route('/edit-task/<task_id>', methods=['GET'])
def editTask(task_id):
    if 'token' not in session:
        return redirect(url_for('home'))

    task = Task.query.filter_by(id=task_id).first()

    if task:
        return render_template('edit_task.html', task=task)
    else:
        return redirect(url_for('tasks'))

# Ruta para actualizar tarea
@app.route('/update-task', methods=['POST'])
def updateTask():
    if 'token' not in session:
        return redirect(url_for('home'))

    task_id = request.form['id']
    title = request.form['title']
    description = request.form['description']

    task = Task.query.filter_by(id=task_id).first()

    if title and description and task:
        task.title = title
        task.description = description
        db.session.commit()

    return redirect(url_for('tasks'))

# Ruta para proyectos
@app.route('/projects', methods=['GET'])
def projects():
    if 'token' not in session:
        return redirect(url_for('home'))

    email = session['email']
    projects = Project.query.filter_by(user_email=email).all()

    projects_list = []
    for project in projects:
        projects_list.append({
            'id': project.id,
            'user_email': project.user_email,
            'title': project.title,
            'description': project.description,
            'start_date': project.start_date,
            'end_date': project.end_date
        })

    return render_template('projects.html', projects=projects_list)

# Ruta para crear nuevo proyecto
@app.route('/new-project', methods=['POST'])
def newProject():
    if 'token' not in session:
        return redirect(url_for('home'))

    title = request.form['title']
    description = request.form['description']
    email = session['email']
    start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    end_date = request.form['end_date']

    if title and description and email:
        new_project = Project(user_email=email, title=title, description=description, start_date=start_date, end_date=end_date)
        db.session.add(new_project)
        db.session.commit()
    return redirect(url_for('projects'))

# Ruta para eliminar proyecto
@app.route("/delete-project", methods=["POST"])
def deleteProject():
    if 'token' not in session:
        return redirect(url_for('home'))
    
    project_id = request.form['id']
    project = Project.query.filter_by(id=project_id).first()
    if project:
        db.session.delete(project)
        db.session.commit()
    return redirect(url_for('projects'))

# Ruta para editar proyecto
@app.route('/edit-project/<project_id>', methods=['GET'])
def editProject(project_id):
    if 'token' not in session:
        return redirect(url_for('home'))

    project = Project.query.filter_by(id=project_id).first()

    if project:
        return render_template('edit_project.html', project=project)
    else:
        return redirect(url_for('projects'))

# Ruta para actualizar proyecto
@app.route('/update-project', methods=['POST'])
def updateProject():
    if 'token' not in session:
        return redirect(url_for('home'))

    project_id = request.form['id']
    title = request.form['title']
    description = request.form['description']
    end_date = request.form['end_date']

    project = Project.query.filter_by(id=project_id).first()

    if title and description and project:
        project.title = title
        project.description = description
        project.end_date = end_date
        db.session.commit()

    return redirect(url_for('projects'))

if __name__ == "__main__":
    
    app.run(debug=True)
