from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'neon-secret-key-change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

import hashlib

@app.template_filter('gravatar')
def gravatar_url(email, size=100, default='robohash', rating='g'):
    if not email:
        email = 'default'
    
    email_encoded = email.strip().lower().encode('utf-8')
    email_hash = hashlib.md5(email_encoded).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d={default}&r={rating}"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) 
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    priority = db.Column(db.String(20), default='low') 
    due_date = db.Column(db.Date, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    stats = {'total': 0, 'completed': 0, 'pending': 0}
    if current_user.is_authenticated:
        tasks = Task.query.filter_by(user_id=current_user.id).all()
        stats['total'] = len(tasks)
        stats['completed'] = len([t for t in tasks if t.is_completed])
        stats['pending'] = stats['total'] - stats['completed']
    return render_template('index.html', stats=stats)

@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        priority = request.form.get('priority')
        due_date_str = request.form.get('due_date')
        
        due_date = None
        if due_date_str:
             due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()

        new_task = Task(title=title, description=description, priority=priority, due_date=due_date, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
        flash('Завдання додано в систему!', 'success')
        return redirect(url_for('tasks'))

    all_tasks = Task.query.filter_by(user_id=current_user.id)\
        .order_by(Task.is_completed.asc(), Task.due_date.asc()).all()
    return render_template('tasks.html', tasks=all_tasks, now=datetime.utcnow().date())

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/api/task/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    task.is_completed = not task.is_completed
    db.session.commit()
    return jsonify({'status': 'success', 'is_completed': task.is_completed})

@app.route('/task/<int:id>/edit', methods=['POST'])
@login_required
def edit_task_full(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('Доступ заборонено!', 'neon-danger')
        return redirect(url_for('tasks'))
    
    task.title = request.form.get('title')
    task.description = request.form.get('description')
    task.priority = request.form.get('priority')
    
    due_date_str = request.form.get('due_date')
    if due_date_str:
        try:
            task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass 
    else:
        task.due_date = None 

    db.session.commit()
    flash('Протокол завдання оновлено.', 'neon-success')
    return redirect(url_for('tasks'))

@app.route('/api/task/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_task_api(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
         return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(task)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email') 
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password_hash=hashed_pw)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Реєстрація успішна! Ласкаво просимо в мережу.', 'neon-success')
            return redirect(url_for('login'))
        except:
            flash('Помилка. Цей логін або email вже зайнято.', 'neon-danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('tasks'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Доступ дозволено. Системи в нормі.', 'neon-success')
            return redirect(url_for('tasks'))
        else:
            flash('Відмова в доступі. Невірні дані.', 'neon-danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вихід із системи завершено.', 'neon-info')
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/form', methods=['GET', 'POST'])
def simple_form():
    if request.method == 'POST':
        name = request.form.get('name')
        return render_template('form.html', name=name)
    return render_template('form.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)