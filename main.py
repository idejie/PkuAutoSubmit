# -*- coding: utf-8
import random
import requests
from urllib.parse import parse_qs
from Const import RequestURL
import os
import json
import datetime


def wechat_notification(uid,appToken, info, str(submit_response),url):
    
    data = {
          "appToken":appToken,
          "content":info,
          "summary":"消息摘要",
          "contentType":1,
          "uids":[uid],
          "url":url
        }
    
    responseBody = requests.post(
        url = RequestURL.wechatNotificationUrl % key,
        data=data
    )
    if responseBody.text == 'ok':
        print('微信提醒发送成功')
    else:
        print('微信提醒发送失败，返回信息：')
        print(responseBody.text)


def update_info(last_info, self_info, dt):

    last_info.update(self_info)

    last_info["dzyx"] = last_info.pop("email")

    last_info.pop("czr")
    last_info.pop("czrq")
    last_info.pop("rowno")
    last_info.pop("shrq")
    last_info.pop("sqlb")
    last_info.pop("sqr")
    last_info.pop("sqrq")
    last_info.pop("sqrqstr")
    last_info.pop("tjr")
    last_info.pop("tjrq")
    last_info.pop("xh")
    last_info.pop("xslb")

    last_info["sqbh"] = ""
    last_info["shbz"] = ""
    last_info["shyj"] = ""
    last_info["ssdm"] = ""
    last_info["tjbz"] = ""
    last_info["lxdh"] = last_info["yddh"]
    last_info["crxrq"] = dt

    last_info["yqc"] = last_info["yqc"].split(',')
    last_info["yqr"] = last_info["yqr"].split(',')

    return last_info


class PkuAccount:
    # 这个类是一个完整类的精简版，要不没必要单独写
    def __init__(self, username: str, passwd: str):
        self._username = username
        self._passwd = passwd
        self._session = requests.Session()
        fake_ua = random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36 Edg/80.0.361.111',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1'])
        self._session.headers.update({
            'User-agent': fake_ua})
        self.alias_dict = {'portal': 'portal2017'}
        self.app_dict = {
            'portal2017': ['https://portal.pku.edu.cn/portal2017/ssoLogin.do', 'https://portal.pku.edu.cn/portal2017/'],
        }

    @property
    def session(self):
        return self._session

    def _get_token(self, appid, otp_code=''):
        if appid in self.alias_dict:
            appid = self.alias_dict[appid]
        auth_url = 'https://iaaa.pku.edu.cn/iaaa/oauthlogin.do'
        auth_dict = {'appid': appid, 'userName': self._username, 'password': self._passwd,
                     'redirUrl': self.app_dict[appid][0], 'otpCode': otp_code}
        return_text = self._session.post(auth_url, data=auth_dict, timeout=7).text

        try:
            return json.loads(return_text)['token']
        except KeyError:
            raise Exception(f'{return_text}\nusername:{self._username}\npassword:{self._passwd}')

    def login(self, appid, otp_code=''):
        if appid in self.alias_dict:
            appid = self.alias_dict[appid]

        token = self._get_token(appid, otp_code=otp_code)
        error = 0
        while error < 4:
            try:
                process_callback = self._session.get(self.app_dict[appid][0], params={
                    'rand': random.random(), 'token': token}, timeout=7)
                return {'success': True, 'token': f'{token}', 'land_url': f'{process_callback.url}',
                        'land_text': f'{process_callback.text}'}
            except:
                error += 1


if __name__ == '__main__':
    username = os.getenv("ID")
    passwd = os.getenv("PASSWORD")
    MAIL_ADDRESS = os.getenv("MAIL_ADDRESS")
    PHONE_NUMBER = os.getenv("PHONE_NUMBER")
    uid = os.getenv("SENDKEY")
    appToken = os.getenv("APPTOKEN")

    pku = PkuAccount(username, passwd)

    pku.login('portal')
    t_1 = pku.session.get('https://portal.pku.edu.cn/portal2017/util/appSysRedir.do?appId=stuCampusExEn')
    token = parse_qs(t_1.url)['token'][0]
    land = pku.session.get(f'https://simso.pku.edu.cn/ssapi/simsoLogin?token={token}')

    sid = json.loads(land.text)['sid']
    xh=json.loads(land.text)['xh']

    r1 = pku.session.get(f'https://simso.pku.edu.cn/pages/sadEpidemicAccess.html?_sk={xh}#/epiAccessHome')
    dt=(datetime.datetime.now() + datetime.timedelta(days = 1)).strftime('%Y%m%d')

    last_info=pku.session.get(f'https://simso.pku.edu.cn/ssapi/stuaffair/epiApply/getSqxxHis?sid={sid}&_sk={xh}&pageNum=1')
    last_info=json.loads(last_info.text)["row"][0]
    self_info=pku.session.get(f'https://simso.pku.edu.cn/ssapi/stuaffair/epiApply/getSqzt?sid={sid}&_sk={xh}')
    self_info=json.loads(self_info.text)["row"]["lxxx"]

    update_info(last_info, self_info, dt)

    r0 = pku.session.post(f'https://simso.pku.edu.cn/ssapi/stuaffair/epiApply/saveSqxx?sid={sid}&_sk={xh}&applyType=yqwf', json=last_info)
    res_0 = json.loads(r0.text)
    if res_0['code'] not in [1, '1']:
        print(f'Failed: {res_0}') # Failed
        wechat_notification(sendkey, str(username)+dt + '预约失败', str(res_0))
        exit(1)

    submit=pku.session.get(f'https://simso.pku.edu.cn/ssapi/stuaffair/epiApply/submitSqxx?sid={sid}&_sk={xh}&sqbh={res_0["row"]}')
    submit_response=json.loads(submit.text)
    if submit_response['code'] in [1, '1'] and submit_response["msg"] == '成功':
        print(f'Success: {submit_response}') # Success
        wechat_notification(uid,appToken, username+dt + '预约成功', str(submit_response),t_1.url)
    else:
        print(f'Failed: {submit_response}') # Failed
        print(f'saveURL return : {res_0}') # Failed
        wechat_notification(uid,appToken, username+dt + '预约失败', str(submit_response),t_1.url)
        exit(1)
