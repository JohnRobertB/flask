from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'  # Use SQLite for simplicity
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(80))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('materials', lazy='dynamic'))
    initial_material = db.Column(db.Float)
    material_per_product = db.Column(db.Float)
    material_used = db.Column(db.Float)

    def __init__(self, user, initial_material, material_per_product, material_used):
        self.user = user
        self.initial_material = initial_material
        self.material_per_product = material_per_product
        self.material_used = material_used

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            return render_template('login.html', error='Invalid username or password.')

        login_user(user)

        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        try:
            initial_material = float(request.form.get('initial_material'))
            material_per_product = float(request.form.get('material_per_product'))
            material_used = float(request.form.get('material_used'))
        except ValueError:
            return render_template('index.html', error='Invalid input. Please enter valid numbers.')

        material = Material(current_user, initial_material, material_per_product, material_used)

        try:
            db.session.add(material)
            db.session.commit()
        except Exception as e:
            return render_template('index.html', error='An error occurred while saving to the database.')

        remaining_material = initial_material - material_used
        possible_products = remaining_material / material_per_product

        low_material_alert = remaining_material < 10  # Change this value to your desired threshold

        return render_template('result.html', remaining_material=remaining_material, possible_products=int(possible_products), low_material_alert=low_material_alert)

    return render_template('index.html')



@app.route('/history')
@login_required
def history():
    materials = Material.query.filter_by(user_id=current_user.id).all()
    return render_template('history.html', materials=materials)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
