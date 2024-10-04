from flask import Flask,flash,request,redirect,render_template,session,url_for
from flask_mail import Mail,Message
from random import *
import base64
import pymysql
import secrets
import bcrypt
import re


app=Flask(__name__)
app.secret_key='ftdjiutcfxdcvcvytftstcd'

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME']='chegenelson641@gmail.com'
app.config['MAIL_PASSWORD']='cfukaomufqorewgu'
app.config['MAIL_USE_TSL']=False
app.config['MAIL_USE_SSL']=True

mail=Mail(app)

connection=pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='flask_mh'
)

cur=connection.cursor()

@app.route('/register',methods=['POST','GET'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        confirm=request.form['confirm']
        cur.execute('SELECT * FROM rio WHERE username=%s',(username))
        connection.commit()
        data=cur.fetchone()
        cur.execute('SELECT * FROM rio WHERE email=%s',(email))
        connection.commit()
        main=cur.fetchone()
        if username=='' or email=='' or password=='' or confirm=='':
            flash('All fields are required','warning')
            return render_template('register.html',username=username,email=email,password=password,confirm=confirm)
        elif data is not None:
            flash('Username already taken create new one','warning')
            return render_template('register.html',username=username,email=email,password=password,confirm=confirm)
        elif main is not None:
            flash('Email already taken cteate new one','warning')
            return render_template('register.html',username=username,email=email,password=password,confirm=confirm)
        elif username==password:
            flash('Password and username should not be simillar','warning')
            return render_template('register.html',username=username,email=email,password=password,confirm=confirm)
        elif password != confirm:
            flash('Incorrect passwords','warning')
            return render_template('register.html',username=username,email=email,password=password,confirm=confirm)
        elif not re.search('[A-Z]',password):
            flash('Password should have capital letters','warning')
            return render_template('register.html',username=username,email=email,password=password,confirm=confirm)
        elif not re.search('[a-z]',password):
            flash('Password should have small characters','warning')
            return render_template('register.html',username=username,email=email,password=password,confirm=confirm)
        else:
            hashed=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
            otp=randint(0000,9999)
            cur.execute('INSERT INTO rio(username,email,password,otp) VALUES(%s,%s,%s,%s)',(username,email,hashed,otp))
            connection.commit()
            subject='Account creation'
            body=f'Thank you for creating an account with us. \n Verify your account {otp}'
            sendmail(subject,email,body)
            flash('Account has been created','success')
            return redirect(url_for('otp'))
        

    return render_template('register.html')
def sendmail(subject,email,body):
    try:
        msg=Message(subject=subject,sender='chegenelson641@gmail.com',recipients=[email],body=body)
        mail.send(msg)
    except Exception as a:
        print(a)


@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        if username=='' or password=='':
            flash('All fields are required','warning')
            return redirect(url_for('login'))
        else:
            cur.execute('SELECT * FROM rio WHERE username=%s',(username))
            connection.commit()
            data=cur.fetchone()
            if data is not None:
                if bcrypt.checkpw(password.encode('utf-8'),data[3].encode('utf-8')):
                    if data[6]==1:
                        session['username']=data[1]
                        session['user_id']=data[0]
                        session['role']=data[4]
                        if session['role']=='patient':
                            return redirect(url_for('dashboard'))
                        else:
                            return redirect(url_for('dashboard'))
                    else:
                        flash('Please verify your account','warning')
                        return redirect(url_for('otp'))
                else:
                    flash('Incorrect password','warning')
                    return redirect(url_for('login'))
            else:
                flash('Incorrect username','warning')
                return redirect(url_for('login'))
            

            
    return render_template('logins.html')


@app.route('/otp',methods=['POST','GET'])
def otp():
    if request.method=='POST':
        otp=request.form['otp']
        cur.execute('SELECT * FROM rio WHERE otp=%s',(otp))
        connection.commit()
        data=cur.fetchone()
        if data is not None:
            cur.execute('UPDATE rio SET is_verified=1 WHERE otp=%s',(otp))
            connection.commit()
            flash('Account has been verified','success')
            return redirect(url_for('login'))
        else:
            flash('Please verify your account','warning')
            return redirect(url_for('otp'))

    return render_template('otp.html')

@app.route('/appoint',methods=['POST','GET'])
def appoint():
    if request.method=='POST':
        user_id=session['user_id']
        doctor=request.form['doctor']
        date=request.form['date']
        phone=request.form['phone']
        patient=request.form['fullname']
        email=request.form['email']
        address=request.form['address']
        cur.execute('INSERT INTO prof(doctor,user_id,date,phone,patient,email,address)VALUES(%s,%s,%s,%s,%s,%s,%s)',(doctor,user_id,date,phone,patient,email,address))
        connection.commit()
        return redirect(url_for('dashboard'))
    return render_template('appoint.html')

@app.route('/')
def dashboard():
    user_id=session['user_id']
    doctor=session['username']
    patient=session['username']
    cur.execute('SELECT * FROM prof WHERE user_id=%s',(user_id))
    connection.commit()
    data=cur.fetchall()
    cur.execute('SELECT * FROM prof WHERE doctor=%s',(doctor))
    connection.commit()
    team=cur.fetchall()
    cur.execute('SELECT * FROM lab WHERE patient=%s',(patient))
    connection.commit()
    tip=cur.fetchall()
    cur.execute('SELECT * FROM schedule WHERE user_id=%s',(user_id))
    connection.commit()
    main=cur.fetchall()
    return render_template('dashboard.html',data=data,team=team,tip=tip,main=main)
@app.route('/chose',methods=['POST','GET'])
def chosen():
    if request.method=='POST':
        # user_id=session['user_id']
        doctor=session['username']
        action=request.form['action']
        cur.execute('UPDATE prof SET action=%s WHERE doctor=%s',(action,doctor))
        connection.commit()
        return redirect(url_for('dashboard'))
        
    return render_template('chose.html')

@app.route('/lab',methods=['POST','GET'])
def lab():
    if request.method=='POST':
        
        user_id=session['user_id']
        test=request.form['test']
        allergies=request.form['allergies']
        patient=request.form['patient']
        medication=request.form['medication']
        method=request.form['method']
        cost=request.form['cost']
        cur.execute('INSERT INTO lab(user_id,test,allergies,patient,medication,method,cost)VALUES(%s,%s,%s,%s,%s,%s,%s)',(user_id,test,allergies,patient,medication,method,cost))
        connection.commit()
        cur.execute('UPDATE prof SET action="done" WHERE patient=%s',(patient))
        connection.commit()
        return redirect(url_for('dashboard'))
    return render_template('lab.html')


@app.route('/logout',methods=['POST','GET'])
def logout():
    session.clear()
    return redirect(url_for('login'))
@app.route('/add',methods=['POST','GET'])
def add():
    if request.method=='POST':
        user_id=session['user_id']
        day=request.form['day']
        morning=request.form['morning']
        morning2=request.form['morning2']
        afternoon=request.form['afternoon']
        evening=request.form['evening']
        cur.execute('INSERT INTO schedule(user_id,day,morning,morning2,afternoon,evening)VALUES(%s,%s,%s,%s,%s,%s)',(user_id,day,morning,morning2,afternoon,evening))
        connection.commit()
        return redirect(url_for('dashboard'))

    return render_template('time.html')



if __name__ in '__main__':
    app.run(debug=True)
