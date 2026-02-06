from flask import Flask, render_template, request, redirect, url_for, session, g, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from datetime import datetime
import os 

app = Flask(__name__)
app.secret_key = 'chave_secreta_para_proteger_suas_sessoes'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cambiofacil.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =======================================================
# MODELOS
# =======================================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    history = db.relationship('ConversionHistory', backref='user', lazy=True)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ConversionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    currency_from = db.Column(db.String(3), nullable=False)
    amount_from = db.Column(db.Float, nullable=False)
    currency_to = db.Column(db.String(3), nullable=False)
    amount_to = db.Column(db.Float, nullable=False)


# =======================================================
# API DE CÂMBIO (RESTAURADA)
# =======================================================

API_KEY = "d2254ad58a0bfb0a366d48f8"
API_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"

def get_exchange_rates():
    fallback_rates = {
        'USD': 1.0, 'BRL': 5.0, 'EUR': 0.9,
        'JPY': 150.0, 'GBP': 0.8, 'CNY': 7.0
    }
    data_cotacao = 'N/A'

    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()

        rates = data.get('conversion_rates', fallback_rates)
        data_cotacao_utc = data.get('time_last_update_utc', 'N/A')

        if data_cotacao_utc != 'N/A':
            try:
                date_string = data_cotacao_utc.split(', ', 1)[1]
                date_only = ' '.join(date_string.split(' ')[:3])
                dt = datetime.strptime(date_only, '%d %b %Y')
                data_cotacao = dt.strftime('%d-%m-%Y')
            except:
                data_cotacao = 'N/A'

        return rates, data_cotacao

    except:
        return fallback_rates, 'N/A'


# =======================================================
# CONTEXTO GLOBAL
# =======================================================

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if not user_id:
        g.user = None
        g.logged_in = False
    else:
        g.user = User.query.get(user_id)
        g.logged_in = True


# =======================================================
# ROTAS
# =======================================================

@app.route('/')
def home():
    return render_template('home.html', title='Câmbio Fácil | Início', logged_in=g.logged_in)


# =======================================================
# ROTA DE CONVERSÃO (CORRIGIDA)
# =======================================================

@app.route('/conversion', methods=['GET', 'POST'])
def conversion():

    valor_input = "0.00"
    valor_convertido = "0.00"
    from_currency = "USD"
    to_currency = "BRL"

    rates, data_cotacao = get_exchange_rates()

    if request.method == 'POST':
        valor_input = request.form.get('valor', "0.00")
        from_currency = request.form.get('from_currency', "USD")
        to_currency = request.form.get('to_currency', "BRL")

        try:
            amount = float(valor_input)

            from_rate = rates.get(from_currency, 1.0)
            to_rate = rates.get(to_currency, 1.0)

            valor_em_usd = amount / from_rate
            valor_convertido_float = valor_em_usd * to_rate
            valor_convertido = f"{valor_convertido_float:.2f}"

            if g.logged_in:
                registro = ConversionHistory(
                    user_id=g.user.id,
                    amount_from=amount,
                    currency_from=from_currency,
                    amount_to=valor_convertido_float,
                    currency_to=to_currency
                )
                db.session.add(registro)
                db.session.commit()

        except:
            valor_convertido = "Valor Inválido"

    return render_template(
        'conversion.html',
        title="Câmbio Fácil | Conversão",
        logged_in=g.logged_in,
        valor_input=valor_input,
        valor_convertido=valor_convertido,
        data_cotacao=data_cotacao,
        from_currency_code=from_currency,
        to_currency_code=to_currency
    )


# =======================================================
# REGISTRO
# =======================================================

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    if User.query.filter_by(email=email).first():
        flash('Este e-mail já está cadastrado.', 'error')
        return redirect(url_for('login') + '#register')

    password_hash = generate_password_hash(password)
    new_user = User(name=name, email=email, password_hash=password_hash)

    try:
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        return redirect(url_for('home'))

    except Exception as e:
        db.session.rollback()
        flash('Erro ao cadastrar.', 'error')
        return redirect(url_for('login') + '#register')


# =======================================================
# LOGIN
# =======================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))

        flash('Usuário ou senha inválidos.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html', title='Câmbio Fácil | Login', logged_in=g.logged_in)


# =======================================================
# SOBRE
# =======================================================

@app.route('/about')
def about():
    return render_template('about.html', title='Câmbio Fácil | Sobre', logged_in=g.logged_in)


# =======================================================
# LOGOUT
# =======================================================

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    g.user = None
    g.logged_in = False
    return redirect(url_for('home'))


# =======================================================
# PERFIL
# =======================================================

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not g.logged_in:
        flash('Faça login para acessar o perfil.', 'warning')
        return redirect(url_for('login'))

    user = g.user
    user_name = user.name
    user_email = user.email

    if request.method == 'POST':
        new_name = request.form.get('name')
        new_email = request.form.get('email')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        try:
            changes = False

            if new_name and new_name != user.name:
                user.name = new_name
                changes = True

            if new_email and new_email != user.email:
                if User.query.filter(User.email == new_email, User.id != user.id).first():
                    flash('E-mail já usado por outra conta.', 'error')
                    return render_template('profile.html', title='Câmbio Fácil | Meu Perfil',
                                           user_name=user.name, user_email=user.email, logged_in=g.logged_in)
                user.email = new_email
                changes = True

            if new_password:
                if new_password == confirm_password:
                    user.password_hash = generate_password_hash(new_password)
                    changes = True
                else:
                    flash('As senhas não coincidem.', 'error')
                    return render_template('profile.html',
                                           title='Câmbio Fácil | Meu Perfil',
                                           user_name=user.name,
                                           user_email=user.email,
                                           logged_in=g.logged_in)

            if changes:
                db.session.commit()
                flash('Perfil atualizado!', 'success')
            else:
                flash('Nenhuma alteração feita.', 'info')

        except:
            db.session.rollback()
            flash('Erro ao atualizar perfil.', 'error')

    return render_template(
        'profile.html',
        title='Câmbio Fácil | Meu Perfil',
        user_name=user_name,
        user_email=user_email,
        logged_in=g.logged_in
    )


# =======================================================
# HISTÓRICO
# =======================================================

@app.route('/history')
def history():
    if not g.logged_in:
        flash('Você precisa estar logado.', 'warning')
        return redirect(url_for('login'))

    user_history = ConversionHistory.query.filter_by(
        user_id=g.user.id).order_by(
        ConversionHistory.timestamp.desc()).all()

    return render_template('history.html',
                           title='Câmbio Fácil | Histórico',
                           logged_in=g.logged_in,
                           user_history=user_history)


# =======================================================
# EXECUÇÃO
# =======================================================

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except:
            pass

    app.run(debug=True)
