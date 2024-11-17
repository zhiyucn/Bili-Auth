from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, send_from_directory, Response
import sqlite3
import requests
import auth
import uuid
import random
import log
import time
import qrcode
import json
import os

logging = log.Log(time.strftime("%Y-%m-%d", time.localtime()) + ".log")
app = Flask(__name__)
app.secret_key = 'dhw82h80H8dwiopusb2udqwef3123'  # 初始密钥，可在管理页面修改

# 初始化 SQLite 数据库
def init_db():
    conn = sqlite3.connect('bili_auth.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_uid TEXT NOT NULL,
            cookies TEXT NOT NULL,
            device_id TEXT NOT NULL,
            csrf TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oauth_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            client_secret TEXT NOT NULL,
            redirect_uri TEXT NOT NULL,
            authorization_url TEXT NOT NULL,
            token_url TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    logging.log("DB_INIT_SUCCESS")

# 检查用户是否登录
def is_logged_in():
    return 'username' in session

@app.route('/')
def index():
    if is_logged_in():
        return redirect(url_for('manage'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin':
            session['username'] = username
            flash('登录成功！', 'success')
            return redirect(url_for('manage'))
        else:
            flash('用户名或密码错误', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('您已成功登出！', 'success')
    return redirect(url_for('login'))

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    if not is_logged_in():
        return redirect(url_for('login'))

    try:
        conn = sqlite3.connect('bili_auth.db')
        cursor = conn.cursor()
        if request.method == 'POST':
            new_secret_key = request.form.get('session_key')
            app.secret_key = new_secret_key  # 修改应用的 secret_key
            
            return redirect(url_for('manage'))

        cursor.execute('SELECT * FROM accounts')
        accounts = cursor.fetchall()
        cursor.execute('SELECT * FROM oauth_configs')
        oauth_configs = cursor.fetchall()
        conn.close()
        return render_template('manage.html', accounts=accounts, oauth_configs=oauth_configs)
    except Exception as e:
        logging.log(f"ERROR: {e}")
        return "发生错误"

@app.route('/add-account', methods=['POST'])
def add_account():
    data = request.form
    sender_uid = data.get('sender_uid')
    cookies = data.get('cookies')
    device_id = data.get('device_id')
    csrf = data.get('csrf')

    conn = sqlite3.connect('bili_auth.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO accounts (sender_uid, cookies, device_id, csrf) VALUES (?, ?, ?, ?)',
                   (sender_uid, cookies, device_id, csrf))
    conn.commit()
    conn.close()

    return redirect(url_for('manage'))

@app.route('/delete-account/<int:id>', methods=['POST'])
def delete_account(id):
    conn = sqlite3.connect('bili_auth.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM accounts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage'))

@app.route('/add-oauth-config', methods=['POST'])
def add_oauth_config():
    data = request.form
    redirect_uri = data.get('redirect_uri')
    authorization_url = data.get('authorization_url')
    token_url = data.get('token_url')

    client_id = str(uuid.uuid4())
    client_secret = str(uuid.uuid4())

    conn = sqlite3.connect('bili_auth.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO oauth_configs (client_id, client_secret, redirect_uri, authorization_url, token_url) VALUES (?, ?, ?, ?, ?)',
                   (client_id, client_secret, redirect_uri, authorization_url, token_url))
    conn.commit()
    conn.close()

    return redirect(url_for('manage'))

@app.route('/delete-oauth-config/<int:id>', methods=['POST'])
def delete_oauth_config(id):
    conn = sqlite3.connect('bili_auth.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM oauth_configs WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage'))
@app.route('/login-oauth/<int:config_id>')  # 确保 config_id 是整数
def login_oauth(config_id):
    # 获取 OAuth2 配置
    conn = sqlite3.connect('bili_auth.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM oauth_configs WHERE id = ?', (config_id,))
    oauth_config = cursor.fetchone()
    conn.close()
    
    if oauth_config:
        client_id = oauth_config[1]  # client_id
        redirect_uri = oauth_config[3]  # redirect_uri
        # 重定向到授权页面
        return redirect(f"/authorize?client_id={client_id}&redirect_uri={redirect_uri}")
    return "无效的配置ID"  # 处理无效配置的情况

@app.route('/authorize', methods=['GET'])
def authorize():
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    
    # 显示授权页面，询问用户是否允许客户端访问
    return render_template('authorize.html', client_id=client_id, redirect_uri=redirect_uri)

@app.route('/approve', methods=['POST'])
def approve():
    client_id = request.form.get('client_id')
    redirect_uri = request.form.get('redirect_uri')

    # 生成授权码
    authorization_code = str(uuid.uuid4())

    # 在这里可以将授权码存储在数据库中，与 client_id 相关联

    # 提示用户已授权并重定向到机器人的B站主页
    flash("您已成功授权！", "success")
    
    # 重定向到随机选择的机器人的 B 站主页
    return redirect(f"/redirect-bot?client_id={client_id}&redirect_uri={redirect_uri}&code={authorization_code}")

@app.route('/redirect-bot', methods=['GET'])
def redirect_bot():
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    code = request.args.get('code')

    # 随机选择一个机器人账号
    conn = sqlite3.connect('bili_auth.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM accounts')
    accounts = cursor.fetchall()
    conn.close()

    if accounts:
        selected_account = random.choice(accounts)  # 随机选择一个机器人账号
        sender_uid = selected_account[1]  # 发送者UID
        cookies = selected_account[2]      # Cookie
        device_id = selected_account[3]    # 设备ID
        csrf = selected_account[4]         # CSRF

        # 跳转到机器人的 B 站主页，并询问用户输入他们的 B 站 UID
        return render_template('request_uid.html', sender_uid=sender_uid, redirect_uri=redirect_uri, code=code)
    
    return "没有可用的机器人账号"

@app.route('/send-code', methods=['POST'])
def send_code():
    target_uid = request.form.get('target_uid')
    code = request.form.get('code')

    # 随机选择一个机器人账号
    conn = sqlite3.connect('bili_auth.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM accounts')
    accounts = cursor.fetchall()
    conn.close()

    if accounts:
        selected_account = random.choice(accounts)  # 随机选择一个机器人账号
        sender_uid = selected_account[1]  # 发送者UID
        cookies = selected_account[2]      # Cookie
        device_id = selected_account[3]    # 设备ID
        csrf = selected_account[4]         # CSRF

        # 调用发验证码的方法
        auth.Auth.send_code(sender_uid, target_uid, cookies, device_id, csrf)

    return redirect(url_for('manage'))

@app.route('/callback')
def callback():
    # 从请求参数中获取授权码
    code = request.args.get('code')

    # 使用授权码向用户发送验证码
    # 具体操作在 send_code 处理，这里不再处理发送逻辑

    return "Callback received"  # 你可以根据需要调整这个返回

@app.route('/test-account', methods=['POST'])
def test_account():
    account_id = request.form.get('account_id')
    target_uid = request.form.get('target_uid')

    if account_id and target_uid:
        # 获取账户信息
        conn = sqlite3.connect('bili_auth.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
        account = cursor.fetchone()
        conn.close()

        if account:
            sender_uid = account[1]  # 发送者UID
            cookies = account[2]      # Cookie
            device_id = account[3]    # 设备ID
            csrf = account[4]         # CSRF
            print(f"sender_uid: {sender_uid}, target_uid: {target_uid}, cookies: {cookies}, device_id: {device_id}, csrf: {csrf}")
            # 调用 Auth 类中的 send_code 方法发送测试消息
            auth.Auth.send_code(sender_uid, target_uid, cookies, device_id, csrf)
            return redirect(url_for('manage'))  # 返回成功的页面或消息

    return redirect(url_for('manage'))  # 处理未选择的情况
qr_code_url = ""
qr_code_key = ""
@app.route('/get-qr-code')
def get_qr_code():
    global qr_code_url, qr_code_key
    headers = {
        'User-Agent':"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
        'Accept_Language':"zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        'Connection':"keep-alive",
        'Referer':"https://passport.bilibili.com/login"
    }
    get = requests.get('https://passport.bilibili.com/x/passport-login/web/qrcode/generate',headers=headers)
    logging.log(get.text)
    if "<!DOCTYPE html>" in get.text:
        logging.log("ERROR_CODE: 10001")
    try:
        code = json.loads(get.text)
        qr_code_url = code['data']['url']
        qr_code_key = code['data']['qrcode_key']
        logging.log(qr_code_url)
        logging.log(qr_code_key)
        img = qrcode.make(qr_code_url)
        os.remove('static/qrcode.png')
        #这里先删除了之前的qrcode.png文件
        img.save('static/qrcode.png')
        return redirect("/qrcode.html")
    except:
        logging.log("QR_CODE_ERROR",'ERROR')
        return "QR_CODE_ERROR"
    #qr_code_url = code['url']
@app.route('/qrcode.png')
def qrcode_png():
    # qrcode.png文件在static文件夹下
    return send_from_directory('static', 'qrcode.png')

@app.route('/qrcode.html')
def qrcode_html():
    # 返回一个包含HTML内容的Response对象
    html_content = "<img src='/qrcode.png' alt='QR Code'><br><br><a href='/qr-code-login'>扫码完毕之后点击</a>"
    return Response(html_content, mimetype='text/html')
@app.route('/qr-code-login')
def qr_code_login():
    global cookie
    headers = {
        'User-Agent':"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
        'Accept_Language':"zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        'Connection':"keep-alive",
        'Referer':"https://passport.bilibili.com/login"
    }
    get = requests.get('https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key='+qr_code_key,headers=headers)
    qr_code_code = json.loads(get.text)
    qr_code_code = qr_code_code['data']["message"]
    logging.log(get.text)
    if "" == qr_code_code:
        logging.log("QR_CODE_LOGIN_SUCCESS")
        cookie = requests.utils.dict_from_cookiejar(get.cookies)
        with open('cookie.txt', 'w') as f:
            f.write(str(cookie))
            #记录cookie到文件
            sender_uid = cookie['DedeUserID']
            csrf = cookie['bili_jct']
            dev_id = str(uuid.uuid4()).upper()
            conn = sqlite3.connect('bili_auth.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO accounts (sender_uid, cookies, device_id, csrf) VALUES (?, ?, ?, ?)',(str(sender_uid), str(cookie), dev_id, csrf))
            conn.commit()
            conn.close()
            return "<p>登录成功！</p>"

        return "<p>登录成功！</p>"
    elif "二维码已失效" == qr_code_code:
        logging.log("QR_CODE_FAILED")
        return "<p>登录失败！二维码失效，请重新获取！</p>"
    elif "二维码已扫码未确认" == qr_code_code:
        logging.log("QR_CODE_WAIT")
        return "<p>登录失败！二维码已扫描，未确认！</p>"
    elif "未扫码" == qr_code_code:
        logging.log("QR_CODE_DONT_LOGIN")
        return "<p>登录失败！未扫描二维码！</p>"
    else:
        logging.log("QR_CODE_ERROR",'ERROR')
        return "QR_CODE_ERROR"
        
if __name__ == '__main__':
    init_db()
    app.run(port=8000)
