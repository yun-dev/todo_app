from flask import Flask,redirect,render_template,session,request,render_template_string,jsonify
import sqlite3

app=Flask(__name__)
app.secret_key="this is todo.py"

def get_connection():
    conn=sqlite3.connect('todoapp.db')
    conn.row_factory=sqlite3.Row
    return conn

# 建库，建表
cn=get_connection()
try:
    cs=cn.cursor()
    sql1='''
    CREATE TABLE "events" (
	`id`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`content`	varchar(255) NOT NULL,
	`status`	INTEGER NOT NULL DEFAULT 0,
	`u_id`	INTEGER
)
    '''
    try:
        cs.execute(sql1)
    except:
        pass
    

    sql2='''
    CREATE TABLE `users` (
	`id`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`name`	varchar(10) UNIQUE,
	`password`	varchar(20) NOT NULL
)
    '''
    try:
        cs.execute(sql2)
    except:
        pass

finally:
    cn.close()

def is_login_success(name,password):
    cn=get_connection()
    try:
        cs=cn.cursor()
        login_flag=cs.execute('select 1 from users where name=(?) and password=(?)',(name,password,)).fetchone()
        if login_flag:
            return True #登录成功
        return False #登录失败，请检查用户名和密码是否正确
    finally:
        cn.close()

def regisiter(name,password):
    cn=get_connection()
    try:
        cs=cn.cursor()
        exist_flag=cs.execute('select 1 from users where name=(?)',(name,)).fetchone()
        if exist_flag:
            return "用户名已存在" #False
        cs.execute('insert into users (name,password) values ((?),(?))',(name,password,))
        cn.commit()
        return "注册成功" #True
    finally:
        cn.close()

def add_event(content,user_name):
    cn=get_connection()
    try:
        cs=cn.cursor()
        user_id=(cs.execute('select id from users where name=(?)',(user_name,)).fetchone())['id']
        cs.execute('insert into events (content,u_id) values ((?),(?))',((content),(user_id),))
        cn.commit()
    finally:
        cn.close()

def change_event_status(id):
    cn=get_connection()
    try:
        cs=cn.cursor()
        status=(cs.execute('select status from events where id=(?)',(id,)).fetchone())['status']
        if status==0:
            cs.execute('update events set status=1 where id=(?)',(id,))
        else:
            cs.execute('update events set status=0 where id=(?)',(id,))
        cn.commit()
    finally:
        cn.close()

def delete_event_by_id(id):
    cn=get_connection()
    try:
        cs=cn.cursor()
        cs.execute('delete from events where id=(?)',(id,))
        cn.commit()
    finally:
        cn.close()

def delete_finished_events(user_name):
    cn=get_connection()
    try:
        cs=cn.cursor()
        user_id=(cs.execute('select id from users where name=(?)',(user_name,)).fetchone())['id']
        cs.execute('delete from events where u_id=(?) and status=1',(user_id,))
        cn.commit()
    finally:
        cn.close()

def update_event(id,update_content):
    cn=get_connection()
    try:
        cs=cn.cursor()
        cs.execute('update events set content=(?) where id=(?)',((update_content),(id),))
        cn.commit()
    finally:
        cn.close()

def count_finished_events(user_name):
    cn=get_connection()
    try:
        cs=cn.cursor()
        user_id=(cs.execute('select id from users where name=(?)',(user_name,)).fetchone())['id']
        count=(cs.execute('select count(id) from events where u_id=(?) and status=0',(user_id,)).fetchone())['count(id)'] 
        return count
    finally:
        cn.close()

def get_events(user_name,status=None):
    '''
    status为None，返回该用户所有的events
    若传入status，则返回对应的events
    '''
    cn=get_connection()
    try:
        cs=cn.cursor()
        user_id=(cs.execute('select id from users where name=(?)',(user_name,)).fetchone())['id']
        if status is None:
            all_events_data=cs.execute('select * from events where u_id=(?)',(user_id,)).fetchall()
        else:
            all_events_data=cs.execute('select * from events where u_id=(?) and status=(?)',(user_id,status,)).fetchall()    
        events=[]
        for i in all_events_data:
            events.append([i['id'],i['content'],i['status'],i['u_id']])
        return events
    finally:
        cn.close()

@app.route('/')
def index():
    if 'clear_session' in request.args:
        session.pop('current_user')
    login_info=session.get('current_user')
    return render_template('index.html',login_info=login_info)

@app.route('/submit',methods=['GET','POST'])
def submit():
    if 'current_user' not in session:
        return jsonify({'status':-1})
    data=request.get_json()
    print(data)
    delete_id=data.get('delete_id')
    change_id=data.get('change_id')
    new_content=data.get('new_content')
    id=data.get('id')
    update_content=data.get('update_content')
    if delete_id=="completed":
        delete_finished_events(session['current_user'])
    elif delete_id:
        delete_event_by_id(delete_id)
    if change_id is not None:
        change_event_status(change_id)
    if new_content:
        add_event(new_content,session['current_user'])
    if update_content:
        update_event(id,update_content)
    events=get_events(session['current_user'],data.get('events'))
    count_finished=count_finished_events(session['current_user'])
    send_data={'status':0,'events':events,'count':count_finished}
    return jsonify(send_data)

@app.route('/register/')
def register():
    return render_template('register.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/check/<int:code_type>/', methods=['GET', 'POST'])
def check(code_type):
    name = request.form.get('name')
    pwd = request.form.get('pwd')
    pwd_again = request.form.get('pwd_again')
    if code_type == 0:
        if pwd is None or pwd=="":
            msg = "密码不能为空"
        elif pwd != pwd_again:
            msg = '两次密码输入需一致'
        else:
            msg=regisiter(name,pwd)
            if msg=="注册成功":
                return render_template_string('<center><p><h2>{{msg}}</h2></p><p><a href="/login" target="_self"><h2>去登录</h2></a></p></center>', msg=msg)
        return render_template('register.html', msg=msg)
    else:
        msg=is_login_success(name,pwd)
        if msg:
            session['current_user'] = name
            return render_template_string(
                '<center><p><h2>{{msg}}</h2></p><p><a href="/" target="_self"><h2>返回</h2></a></p></center>',
                msg="登录成功")
        return render_template_string('<center><p><h2>{{msg}}</h2></p><p><a href="/login" target="_self"><h2>返回</h2></a></p></center>', msg="登录失败，请检查用户名和密码是否正确")


if __name__=='__main__':
    app.run(debug=True)
