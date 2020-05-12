from flask import Flask, render_template, flash, request, session, url_for, session
from config import Config
from functools import wraps
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message
from wtforms import Form, StringField, TextAreaField, BooleanField, PasswordField, validators
from wtforms.fields.html5 import EmailField
from wtforms.widgets import TextArea
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config.from_object(Config)

mail = Mail(app)
mysql = MySQL(app)


# Email Confirmations
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except SignatureExpired:
        return 'The Token is expired'
    except:
        return False
    return email

@app.route('/confirm_email/<token>')
def confirm_email(token):
    email = confirm_token(token)

    if (email == False):
        flash('Your email could not be verified', 'danger')
        return render_template('login.html', title = 'Login')
    else:
        # DB ADD the Verified Email Flag
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE IATAUsers SET email_verified = 1 WHERE email = %s', [email])
        
        mysql.connection.commit()
        cursor.close()
        
        flash('Your email has been successfully verified', 'success')
        return render_template('login.html', title = 'Login')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, Please Login", 'danger')
            return render_template('login.html', title = 'Login')
    return wrap


@app.route('/', methods = ['GET', 'POST'])
@app.route('/signIn', methods=['GET', 'POST'])
def index():
    return render_template('login.html', title = 'Login')

@app.route('/home', methods = ['GET', 'POST'])
def home():
    return render_template('index.html', title = 'Home')


@app.route('/iatar', methods=['GET', 'POST'])
def iatar():
    return render_template('registerIata.html', title = 'Register')


@app.route('/customerr', methods=['GET', 'POST'])
def customerr():
    return render_template('rcustomer.html', title = 'Register')

@app.route('/registerI', methods = ['GET', 'POST'])
def registerI():
    if request.method == 'POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']
        password = request.form['password']
        iatacode = request.form['IATACode']
        agencyName = request.form['agencyName']
        phoneN = request.form['phoneN']
        address = request.form['address']
        country = request.form['country']
        city = request.form['city']
        
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * From IATAUsers where email = %s', [email])
        data = cursor.fetchall()
        cursor.execute('SELECT * From Customers where email = %s', [email])
        data2 = cursor.fetchall()

        if len(data) == 0 and len(data2) == 0:
            token = generate_confirmation_token(email)
            msg = Message(
            'Confirm Email',
            sender='koolbhavya.epic@gmail.com',
            recipients=[email])
            link = url_for('confirm_email', token=token, _external=True)
            msg.body = 'Confirm your email by clicking this link:- {}'.format(link)
            mail.send(msg)

            cursor.execute("INSERT INTO IATAUsers(firstName, lastName, email, password, IATACode, agencyName, phone, address, country, city) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (firstName, lastName, email, password, iatacode, agencyName, phoneN, address, country, city))
        else:
            flash('Email Already Registered', 'danger')
            return render_template('registerIata.html', title = "Register")

        mysql.connection.commit()
        cursor.close()

        flash('You are now registered and can log in', 'success')
        return render_template('login.html', title = 'Login')


@app.route('/registerC', methods = ['GET', 'POST'])
def registerC():
    if request.method == 'POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']
        password = request.form['password']
        phoneN = request.form['phoneN']
        address = request.form['address']
        country = request.form['country']
        city = request.form['city']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * From Customers where email = %s', [email])
        data = cursor.fetchall()
        cursor.execute('SELECT * From IATAUsers where email = %s', [email])
        data2 = cursor.fetchall()

        if len(data) == 0 and len(data2) == 0:
            token = generate_confirmation_token(email)
            msg = Message(
            'Confirm Email',
            sender='koolbhavya.epic@gmail.com',
            recipients=[email])
            link = url_for('confirm_email', token=token, _external=True)
            msg.body = 'Confirm your email by clicking this link:- {}'.format(link)
            mail.send(msg)
            cursor.execute("INSERT INTO Customers(firstName, lastName, email, password, phone, address, country, city) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",
                           (firstName, lastName, email, password, phoneN, address, country, city))
        else:
            flash('Email Already Registered', 'danger')
            return render_template('rcustomer.html', title="Register")

        mysql.connection.commit()
        cursor.close()

        flash('You are now registered and can log in', 'success')
        return render_template('login.html', title='Login')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * From IATAUsers where email = %s", [email]) 
        result = cursor.fetchall()
        
        cursor.execute('SELECT * From Customers where email = %s', [email])
        data2 = cursor.fetchall()

        if len(result) == 0 and len(data2) == 0:
            error = 'Email not registered'
            return render_template('login.html', error = error)
        else:
            result = result[0]
            password_match = result['password']
            
            if (password == password_match):
                session['logged_in'] = True
                session['email'] = email
                session['firstName'] = result['firstName']
                
                if len(result) == 0:
                    session['userType'] = 'customer'
                else:
                    session['userType'] = 'iatauser'

                print(session)
                flash('You are now logged in', 'success')
                return render_template('index.html')
            else:
                error = 'Passwords did not match'
                return render_template('login.html', error = error)

@app.route('/forgotpassword', methods = ['GET', 'POST'])
def forgotpassword():
    return render_template('forgotpasswordreq.html', title = 'forgotpassword')

@app.route('/passwordupdatereq', methods = ['GET', 'POST'])
def passwordupdatereq():
    email = request.form['email']

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From IATAUsers where email = %s', [email])
    data1 = cursor.fetchall()

    cursor.execute('SELECT * From Customers where email = %s', [email])
    data2 = cursor.fetchall()

    if len(data1) == 0 and len(data2) == 0:
        flash('Email not registered', 'danger')
        return render_template('login.html', title='Login')
    else:
        token = generate_confirmation_token(email)
        msg = Message(
            'Update Password',
            sender = 'koolbhavya.epic@gmail.com',
            recipients = [email])
        link = url_for('passwordupdate', token = token, _external=True)
        msg.body = 'Change your password by clicking this link:- {}'.format(link)
        mail.send(msg)

        flash('Kindly Check your email', 'success')
        return render_template('login.html', title = 'Login')


@app.route('/passwordupdate/<token>', methods = ['GET', 'POST'])
def passwordupdate(token):
    email = confirm_token(token)

    return render_template('forgotpassword.html', email = email)

@app.route('/passwordupdatef', methods = ['GET', 'POST'])
def passwordupdatef():
    email = request.form['email']
    password = request.form['password']

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From IATAUsers where email = %s', [email])
    data1 = cursor.fetchall()

    cursor.execute('SELECT * From Customers where email = %s', [email])
    data2 = cursor.fetchall()

    if len(data1) == 0:
        cursor.execute('UPDATE Customers SET password = %s where email = %s', [password, email])
    else:
        cursor.execute('UPDATE IATAUsers SET password = %s where email = %s', [password, email])

    mysql.connection.commit()
    cursor.close()
    flash('Your password has been updated', 'success')
    return render_template('login.html', title = 'Login')


if __name__ == "__main__":
    app.run(debug = True)

'''
Change navbar after login (adding menu bars) 
'''
