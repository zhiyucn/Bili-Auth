from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
import requests
from auth import Auth  # 引入 Auth 类

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 初始密钥，可在管理页面修改

# 初始化SQLite数据库
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    conn = sqlite3.connect('bili_auth.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        # 更新会话密钥
        new_secret_key = request.form.get('session_key')
        app.secret_key = new_secret_key  # 修改应用的secret_key

        return redirect(url_for('manage'))

    cursor.execute('SELECT * FROM accounts')
    accounts = cursor.fetchall()
    cursor.execute('SELECT * FROM oauth_configs')
    oauth_configs = cursor.fetchall()
    conn.close()
    return render_template('manage.html', accounts=accounts, oauth_configs=oauth_configs)

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
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    redirect_uri = data.get('redirect_uri')
    authorization_url = data.get('authorization_url')
    token_url = data.get('token_url')

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

@app.route('/login-oauth/<int:config_id>')
def login_oauth(config_id):
    # 获取OAuth2配置
    conn = sqlite3.connect('bili_auth.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM oauth_configs WHERE id = ?', (config_id,))
    oauth_config = cursor.fetchone()
    conn.close()

    if oauth_config:
        client_id = oauth_config[1]  # client_id
        redirect_uri = oauth_config[3]  # redirect_uri
        return redirect(f"{oauth_config[4]}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}")

@app.route('/callback')
def callback():
    # 从请求参数中获取授权码
    code = request.args.get('code')

    # 示例：使用授权码换取access token
    response = requests.post(session['token_url'], data={
        'grant_type': 'authorization_code',
        'code': code,
        # 这里添加其他必要的参数
    })

    response_data = response.json()
    access_token = response_data.get('access_token')

    # 将access token存入会话
    session['access_token'] = access_token

    return redirect(url_for('manage'))

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
            auth = Auth()
            auth.send_code(sender_uid, target_uid, cookies, device_id, csrf)
            return redirect(url_for('manage'))  # 返回成功的页面或消息

    return redirect(url_for('manage'))  # 处理未选择的情况

if __name__ == '__main__':
    init_db()
    app.run(port=8000)
