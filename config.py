class Config:
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'  # Base de datos SQLite
    SQLALCHEMY_TRACK_MODIFICATIONS = False