import requests
import random
import time
import log
logging = log.Log(time.strftime("%Y-%m-%d", time.localtime())+".log")
logging.log("AUTH RUNNING", "INFO")
verify_code = ""
class Auth:
    def __init__(self):
        pass
    #这里发送验证码
    def send_code(sender_uid,receiver_uid,cookies,device_id,csrf):
        global verify_code
        vetify_code = str(random.randint(100000,999999))
        content = f"[Bili-Auth]您的验证码为：{vetify_code}，请在10分钟内输入。"
        print(content)
        url = "https://api.vc.bilibili.com/web_im/v1/web_im/send_msg"
        #这就是B站发送私信的API接口，我刚爬到的（其实刚才还有一些URL参数，不过我测试过，没有也可以）
        data = {
        "msg[sender_uid]": sender_uid,
        "msg[receiver_id]": receiver_uid,
        "msg[receiver_type]": 1,
        "msg[msg_type]": 1,
        "msg[msg_status]": 0,
        "msg[content]": f'{{"content":"[Bili-Auth]您的验证码为：{vetify_code}"}}',
        "msg[timestamp]": int(time.time()),
        "msg[new_face_version]": 0,
        "msg[dev_id]": device_id,
        "from_firework": 0,
        "build": 0,
        "mobi_app": "web",
        "csrf_token": csrf,
        "csrf": csrf
    }
        print(data)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
            "Cookie": cookies
        }
        response = requests.post(url, headers=headers, data=data)
        print(response.text)
        print("状态码:", response.status_code)
        print("响应内容:", response.text)
        if response.text == '{"code":-111,"message":"csrf 校验失败","ttl":1}':
            logging.log("CSRF_ERROR", "WARNING")
        elif '"code":0' in response.text:
            logging.log("SEND_CODE_SUCCESS:"+vetify_code, "INFO")
        elif '-101' in response.text:
            logging.log("COOKIE_ERROR", "WARNING")
        else:
            logging.log("UNKNOWN_ERROR", "ERROR")

    def test_code(code):
        if len(code) == 6 and code == verify_code:
            logging.log("TRUE")
            return True
        else:
            logging.log("FALSE")
            return False