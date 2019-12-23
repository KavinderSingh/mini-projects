from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from data import Articles
from flask_mysqldb import MySQL
import MySQLdb
from wtforms import Form, StringField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
app = Flask(__name__)

#configuring MySQL
app.config['MySQL_HOST'] = 'localhost'
app.config['MySQL_USER'] = 'kavi'
app.config['MySQL_PASSWORD'] = '12345'
app.config['MySQL_DB'] = 'flaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' 


mysql = MySQL(app)

Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html', articles = Articles)

@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', id = id)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min = 1, max = 50)])
    username = StringField('Username', [validators.Length(min = 4, max = 25)])
    email = StringField('Email', [validators.Length(min=10, max = 50)])
    password = PasswordField('Password',[
            validators.DataRequired(),  #check whether the data is a true value or not 
            validators.EqualTo('confirm', message = 'Passwords do not match') #documentation
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods = ['GET', 'POST'])

def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))


        # defining cursor

        cur = mysql.connection.cursor()

        cur.execute("USE flaskapp")

        # try to add a constraint to not to allow repeated usernames and names in DB

        cur.execute("INSERT INTO users(name, email, username, password) VALUES (%s, %s, %s, %s)", (name, email, username, password))

        #commit to the Database
        mysql.connection.commit()

        #close connection
        cur.close()

        #flash message
        flash("Registration Successful!", "success")

        return redirect(url_for('register'))

    return render_template('register.html', form = form)

# login
@app.route('/login', methods = ['GET','POST'])

def login():
    if request.method == 'POST':
        # get form data/fields
        username = request.form['username']
        password_user = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute("USE flaskapp")

        result = cur.execute("SELECT * FROM users WHERE username = %s LIMIT 1" , [username])

        if(result > 0):
            data = cur.fetchone()  #fetchone()
            password = data['password']

            if(sha256_crypt.verify(password_user, password)):
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid login"
                return render_template('login.html', error=error)

            #close the connection
            cur.close()
        else:
            error = "User not found"
            return render_template('login.html', error=error)
    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorised, please first login", 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', "success")

    return redirect(url_for('login'))

if __name__ == '__main__':
    app.secret_key = 'secret'
    app.run(debug= True)
