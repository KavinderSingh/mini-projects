from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
#from data import Articles
from flask_mysqldb import MySQL
import MySQLdb
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
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

#Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    #create cursor
    cur = mysql.connection.cursor()

    cur.execute("USE flaskapp")

    result = cur.execute("SELECT * from articles")

    articles = cur.fetchall()

    cur.close()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
       # msg = '''No articles found. login/register to add new articles'''
        flash("No Articles Found","success")
        return render_template('articles.html')


@app.route('/article/<string:id>/')
def article(id):
     #create cursor
    cur = mysql.connection.cursor()

    cur.execute("USE flaskapp")


    # get article
    cur.execute("SELECT * from articles WHERE id=%s", [id])

    article = cur.fetchone()

    cur.close()

    return render_template('article.html', article = article)


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

        # logic to not to allow 2 same usernames

        result =  cur.execute("SELECT username from users where username=%s", [username])

        if result > 0:
            flash("username already exists", 'danger')
            cur.close()
            return redirect(url_for('register'))

        

        cur.execute("INSERT INTO users(name, email, username, password) VALUES (%s, %s, %s, %s)", (name, email, username, password))

        #commit to the Database
        mysql.connection.commit()

        #close connection
        cur.close()

        #flash message
        flash("Registration Successful!", "success")

        return redirect(url_for('register'))

    return render_template('register.html', form = form)

# USER LOGIN
@app.route('/login', methods = ['GET','POST'])

def login():
    if request.method == 'POST':
        # get form data/fields

        if request.form['username'] == "" or request.form['password'] == "":
            flash("Fill all the fields to login", 'danger')
            return redirect(url_for('login'))

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
                flash('You are now logged in', "success")
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

@app.route('/logout')
@is_logged_in

def logout():
    session.clear()
    flash('You are now logged out', "success")

    return redirect(url_for('login'))


@app.route('/dashboard')
@is_logged_in

def dashboard():

    #create cursor
    cur = mysql.connection.cursor()

    cur.execute("USE flaskapp")

    result = cur.execute("SELECT * from articles")

    articles = cur.fetchall()

    cur.close()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        #msg = 'No articles found'
        return render_template('dashboard.html')


class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min = 1, max = 50)])
    body = TextAreaField('Body', [validators.Length(min=30)])


@app.route('/add_article', methods = ['GET', 'POST'])
@is_logged_in

def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #create a cursor
        cur = mysql.connection.cursor()

        #execute query
        cur.execute("USE flaskapp")

        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        #commit to the database
        mysql.connection.commit()

        #close cursor
        cur.close()

        flash('Article Submitted', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# EDIT ARTICLE

@app.route('/edit_article/<string:id>', methods = ['GET', 'POST'])
@is_logged_in

def edit_article(id):

    cur = mysql.connection.cursor()

    # select the article to be edited by its id
    cur.execute("USE flaskapp")
    cur.execute("SELECT * FROM articles where id = %s", [id])

    article = cur.fetchone()

    form = ArticleForm(request.form)

    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #create a cursor
        cur = mysql.connection.cursor()

        #execute query
        cur.execute("USE flaskapp")

        cur.execute("UPDATE articles SET title = %s, body = %s WHERE id = %s", (title, body, id))


        #commit to the database
        mysql.connection.commit()

        #close cursor
        cur.close()

        flash("Article edited", "success")

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

    # DELETE ARTICLE

@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    #create cursor
    cur = mysql.connection.cursor()

    #select database
    cur.execute("USE flaskapp")

    #execute delete query
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    cur.execute("ALTER TABLE articles AUTO_INCREMENT = %s",[int(id)])
    #commit to the database
    mysql.connection.commit()

    #close the cursor
    cur.close()

    flash("Article deleted", "success")

    return redirect(url_for('dashboard'))
    

if __name__ == '__main__':
    app.secret_key = 'secret'
    app.run(debug= True)
