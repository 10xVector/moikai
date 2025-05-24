from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class Dummy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

admin = Admin(app, name='Test Admin', template_mode='bootstrap4')
admin.add_view(ModelView(Dummy, db.session))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=8080) 