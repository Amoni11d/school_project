from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from flask_socketio import SocketIO, emit


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\projects\\school_project\\site.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
socketio = SocketIO(app)


class GameResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_number = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Модель пользователя
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    games_played = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    game_results = db.relationship('GameResult', backref='user', lazy=True)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    message = request.form.get('message')
    if message:
        # Сохранение сообщения в базу данных
        new_message = Message(sender='User', content=message)
        db.session.add(new_message)
        db.session.commit()
        # Перенаправление пользователя обратно на главную страницу
        return redirect(url_for('home'))
    else:
        # Обработка случая, если сообщение не было передано
        return "Ошибка: Сообщение не было передано"

@app.route('/')
def home():
    return render_template('main.html')

@app.route('/game_1')
def game():
    return render_template('game.html', stage=1)

@app.route('/next_stage_5', methods=['GET'])
def next_stage_5():
    stage = int(request.args.get('stage', 1))
    if stage < 5:
        return render_template('game.html', stage=stage)
    else:
        return render_template('game.html', stage=6)

@app.route('/check_answer_5', methods=['POST'])
def check_answer_5():
    stage = int(request.form.get('stage'))
    answer = request.form.get('answer')
    
    correct_answers = {
        1: '54',
        2: '8',
        3: '8',
        4: '6',
        5: '5',
        6: '6'
    }
    
    if answer == correct_answers.get(stage):
        next_stage = stage + 1
        if next_stage <= 5:
            return jsonify(result=True, next_stage=next_stage)
        else:
            return jsonify(result=True, next_stage=None)
    else:
        return jsonify(result=False)

# Инициализация Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('profile'))
    return render_template('login.html')

@app.route('/profile')
@login_required
def profile():
    user = current_user
    game_results = [result.game_number for result in user.game_results]
    return render_template('profile.html', user=user, game_results=game_results)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Проверим, что пользователь с таким именем не существует
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Такое имя уже используется. Пожалуйста попробуйте другое.', 'danger')
            return render_template('login.html')
        else:
            # Создаем нового пользователя
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()

            flash('Учетная запись успешно создана! Теперь вы можете войти в систему.', 'success')
            return redirect(url_for('login'))

    return render_template('login.html')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50))
    content = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/feedback')
def index():
    return render_template('feedback.html')

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Доступ запрещен. У вас нет разрешения на просмотр этой страницы.', 'danger')
        return redirect(url_for('home'))

    messages = Message.query.all()
    return render_template('admin.html', messages=messages)

@socketio.on('message')
def handle_message(data):
    sender = data['sender']
    content = data['content']
    message = Message(sender=sender, content=content)
    db.session.add(message)
    db.session.commit()
    emit('message', data, broadcast=True)

@app.route('/game_complete/<int:game_number>', methods=['POST'])
@login_required
def game_complete(game_number):
    user = current_user
    game_result = GameResult(user_id=user.id, game_number=game_number)
    db.session.add(game_result)
    user.games_played += 1
    db.session.commit()
    return jsonify({'message': 'Результат игры успешно записан'})

@app.route('/game_2')
def game_2():
    return render_template('game_2.html', stage=1)

@app.route('/next_stage', methods=['GET'])
def next_stage():
    stage = int(request.args.get('stage', 1))
    if stage < 5:
        return render_template('game_2.html', stage=stage)
    else:
        return render_template('game_2.html', stage=6)

@app.route('/check_answer', methods=['POST'])
def check_answer():
    stage = int(request.form.get('stage'))
    answer = request.form.get('answer')
    
    correct_answers = {
        1: '572080',
        2: '700',
        3: '600',
        4: '12',
        5: '9',
        6: '10'
    }
    
    if answer == correct_answers.get(stage):
        next_stage = stage + 1
        if next_stage <= 5:
            return jsonify(result=True, next_stage=next_stage)
        else:
            return jsonify(result=True, next_stage=None)
    else:
        return jsonify(result=False)
    
@app.route('/game_3')
def game_3():
    return render_template('game_3.html', stage=1)

@app.route('/next_stage_1', methods=['GET'])
def next_stage_2():
    stage = int(request.args.get('stage', 1))
    if stage < 5:
        return render_template('game_3.html', stage=stage)
    else:
        return render_template('game_3.html', stage=6)

@app.route('/check_answer_1', methods=['POST'])
def check_answer_2():
    stage = int(request.form.get('stage'))
    answer = request.form.get('answer')
    
    correct_answers = {
        1: '20',
        2: '98',
        3: '840',
        4: '0',
        5: '9',
        6: '10'
    }
    
    if answer == correct_answers.get(stage):
        next_stage = stage + 1
        if next_stage <= 5:
            return jsonify(result=True, next_stage=next_stage)
        else:
            return jsonify(result=True, next_stage=None)
    else:
        return jsonify(result=False)
    
@app.route('/game_4')
def game_4():
    return render_template('game_4.html', stage=1)

@app.route('/next_stage_3', methods=['GET'])
def next_stage_3():
    stage = int(request.args.get('stage', 1))
    if stage < 5:
        return render_template('game_4.html', stage=stage)
    else:
        return render_template('game_4.html', stage=6)

@app.route('/check_answer_2', methods=['POST'])
def check_answer_3():
    stage = int(request.form.get('stage'))
    answer = request.form.get('answer')
    
    correct_answers = {
        1: '789',
        2: '7',
        3: '5',
        4: '1',
        5: '9',
        6: '10'
    }
    
    if answer == correct_answers.get(stage):
        next_stage = stage + 1
        if next_stage <= 5:
            return jsonify(result=True, next_stage=next_stage)
        else:
            return jsonify(result=True, next_stage=None)
    else:
        return jsonify(result=False)
    
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin_password = 'your_admin_password'
            admin = User(username='admin', password=admin_password, is_admin=True)
            db.session.add(admin)
            db.session.commit()
        socketio.run(app, debug=False,)