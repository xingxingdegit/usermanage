#!/home/www/python/bin/python3

# <create> -u 用户名，-U 显示的名称， -e 邮箱  -o 输出的文件名称
# -u 用户名可以省略， 会从邮箱那里取出来
# -o 也可以省略， 默认是 用户名.txt
# -e 邮箱必须指定。
# <offline> -u 登录用户名。 git用户设置block, wiki用户设置禁用， dms用户删除。
# <delete> -u 登录用户名，删除用户
# <disable> and <enable> just for git and wiki. 
# .. disable ->  git block,   wiki 禁用。   功能跟offline中git和wiki的操作一样。
# .. enable  ->  git unblok,   wiki 启用。
# <resetpd> 重置密码暂时只支持ali
# -g 操作git用户，  -m 操作ali用户.   -c 操作wiki用户.  指定哪些用户操作哪些用户

# 创建用户: python3 create.py create [-u test] -U 测试 -e test@test.com -g -m -c
# 重置密码ali: python3 create.py resetpd -u <username> -m
# 删除用户: python3 create.py delete -u <username> -g -m -c
# 下线用户: python3 create.py offline -u <username> -g -m -c
# 失效用户: python3 create.py disable -u <username> -g -c
# 启用用户: python3 create.py unblock -u <username> -g -c


import requests
import sys
import random
import string
import traceback

gitlab_setting = {
    'url': '',   # gitlab url,  http://.....
    'private_token': '',  # 提供登录的private_token
}
# http
git_api = {
    'users': '/api/v4/users',
    'block': '/api/v4/users/{}/block',  # {}需要用户id
    'unblock': '/api/v4/users/{}/unblock',  # {}需要用户id
    'delete': '/api/v4/users/{}', # {}需要用户ID
}

wiki_setting = {
    'url': 'http://wiki.lanjinrong.com',
    'user': '',   # confluence 登录用户密码
    'passwd': '',
}
# xml rpc
# https://developer.atlassian.com/server/confluence/confluence-xml-rpc-and-soap-apis/#remote-api-version-1-and-version-2
# https://developer.atlassian.com/server/confluence/remote-confluence-methods/#authentication-methods
# https://docs.atlassian.com/ConfluenceServer/javadoc/7.12.1/com/atlassian/confluence/rpc/soap/ConfluenceSoapService.html
wiki_api = {
}

ali_setting = {
    'login_url': 'https://signin.aliyun.com/login.htm',
    'api_url': 'ims.aliyuncs.com',
    'akid': '',  # ali access id  key
    'akkey': ''
}
# http, in ali modular
ali_api = {
}

# 采集参数
# 长度有两个功能，
# 1、是1的话，参数值就是布尔, 2的话，值就是下一个索引的值
# 2、参数索引跳过的长度
argv_peer = {
    '-u': ('username', 2),
    '-U': ('name', 2),
    '-e': ('email', 2),
    '-g': ('gituser', 1),
    '-m': ('aliuser', 1),
    '-c': ('wikiuser', 1),
    '-o': ('outfile', 2),
}
argv_data = {
    'otype': None,
    'username': None,
    'name': None,
    'email': None,
    'outfile': None,
    'gituser': None,
    'aliuser': None,
    'wikiuser': None,
}

def argv_parse():
    '''
    -u 登录用户名
    -U 显示用户名
    -e email
    -o out file
    '''
    try:
        argv = sys.argv[1:]
        argv_data['otype'] = sys.argv[1]
        argv = sys.argv[2:]
        i = 0
        while i < len(argv):
            argv_obj, step = argv_peer[argv[i]]
            if step == 1:
                argv_data[argv_obj] = True
                i += 1
            elif step == 2:
                argv_data[argv_obj] = argv[i+1]
                i += 2
            else:
                print('{} Unrecognized'.format(argv[i]))
                return False
        
        if argv_data['username'] is None and argv_data['email'] is not None:
            argv_data['username'] = argv_data['email'].split('@')[0]
        if argv_data['outfile'] is None:
            argv_data['outfile'] = '{}.txt'.format(argv_data['username'])

        return True
    except Exception:
        traceback.print_exc()
        return False

if argv_parse() is not True:
    exit(1)

def get_passwd(num=22):
    string_pool = string.printable[:62]
    password = ['*'] * (num-3)
    for i, n in enumerate(password):
        password[i] = random.choice(string_pool)
    password.append(random.choice(string.ascii_uppercase))
    password.append(random.choice(string.ascii_lowercase))
    password.append(random.choice(string.digits))
    return ''.join(password)

class gitUserManage:
    def __init__(self, username, name=None, email=None):
        # username is login name,   name is show name
        self.name = name
        self.username = username
        self.email = email

    def get_user(self):
        params = {
            'private_token': gitlab_setting['private_token'],
            'username': self.username,
        }
        git_url = '{}/{}'.format(gitlab_setting['url'], git_api['users'])
        resp_data = requests.get(git_url, params=params)
        if resp_data.ok:
            user_data = resp_data.json()
            return user_data
        print(resp_data.text)
        return False

    def create_user(self):
        git_passwd = get_passwd()
        self.passwd = git_passwd
        request_data = {
            'private_token': gitlab_setting['private_token'],
            'email': self.email,
            'password': git_passwd,
            'username': self.username,
            'name': self.name,
            'skip_confirmation': True,
        }
        git_url = '{}/{}'.format(gitlab_setting['url'], git_api['users'])
        resp_data = requests.post(git_url, json=request_data)
        if resp_data.ok:
            print('git create_user: ', True)
            print('git user: {}'.format(self.username))
            print('git password: {}'.format(self.passwd))
            return True
        print(resp_data.text)

    def block_user(self):
        user_info = self.get_user()
        if user_info:
            id = user_info[0]['id']
        else:
            return False

        api_param = git_api['block'].format(id)
        git_url = '{}{}'.format(gitlab_setting['url'], api_param)
        print(git_url)
        request_data = {
            'private_token': gitlab_setting['private_token'],
        }
        resp_data = requests.post(git_url, json=request_data)
        print(resp_data)

    def unblock_user(self):
        user_info = self.get_user()
        if user_info:
            id = user_info[0]['id']
        else:
            return False

        api_param = git_api['unblock'].format(id)
        git_url = '{}{}'.format(gitlab_setting['url'], api_param)
        print(git_url)
        request_data = {
            'private_token': gitlab_setting['private_token'],
        }
        resp_data = requests.post(git_url, json=request_data)
        print(resp_data)
    
    def delete_user(self):
        user_info = self.get_user()
        if user_info:
            id = user_info[0]['id']
        else:
            return False
        api_param = git_api['delete'].format(id)
        git_url = '{}{}'.format(gitlab_setting['url'], api_param)
        print(git_url)
        request_data = {
            'private_token': gitlab_setting['private_token'],
        }
        resp_data = requests.delete(git_url, json=request_data)
        print(resp_data)

    def write_file(self, filename=None):
        with open(filename, 'a') as fd:
            fd.write('gitlab url: {}\n'.format(gitlab_setting['url']))
            fd.write('git user: {}\n'.format(self.username))
            fd.write('git password: {}\n'.format(self.passwd))
            fd.write('----------\n')


from xmlrpc.client import ServerProxy
class confluenceUserManage(ServerProxy):
    def __init__(self, username, name=None, email=None):
        self.username = username
        self.name = name
        self.email = email
        self.isclose = True
    
    def __del__(self):
        if self.isclose is False:
            self.close()

    def create_connect(self):
        try:
            self.client = ServerProxy("{}/rpc/xmlrpc".format(wiki_setting['url']))
            self.token = self.client.confluence2.login(wiki_setting['user'], wiki_setting['passwd'])
            self.isclose = False
            return True
        except Exception:
            traceback.print_exc()
            return False

    def get_user(self):
        try:
            resp_data = self.client.confluence2.getUserInformation(self.token, self.username)
#            resp_data = self.client.confluence2.getUserByName(self.token, self.username)
            return resp_data
        except Exception:
#            traceback.print_exc()
            return False
    def create_user(self):
        wiki_passwd = get_passwd()
        self.passwd = wiki_passwd
        userinfo = {
            'name': self.username,
            'fullname': self.name,
            'email': self.email,
        }
        resp_data = self.client.confluence2.addUser(self.token, userinfo, wiki_passwd)
        print('wiki create_user: ', resp_data)
        if resp_data:
            print('wiki user: {}'.format(self.username))
            print('wiki password: {}'.format(self.passwd))
            return True

    def delete_user(self):
        resp_data = self.client.confluence2.removeUser(self.token, self.username)
        if resp_data:
            return True
        return False

    # 禁用用户
    def deactivate_user(self):
        resp_data = self.client.confluence2.deactivateUser(self.token, self.username)
        if resp_data:
            return True
        return False

    # 启用用户
    def reactivate_user(self):
        resp_data = self.client.confluence2.reactivateUser(self.token, self.username)
        if resp_data:
            return True
        return False

    def logout(self):
        self.client.confluence2.logout(self.token)
    def close(self):
        if self.isclose is False:
            self.logout()
            self.client.__exit__()
            self.isclose = True
    def write_file(self, filename=None):
        with open(filename, 'a') as fd:
            fd.write('wiki url: {}\n'.format(wiki_setting['url']))
            fd.write('wiki user: {}\n'.format(self.username))
            fd.write('wiki password: {}\n'.format(self.passwd))


from alibabacloud_ims20190815.client import Client as Ims20190815Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ims20190815 import models as ims_20190815_models

class aliUserManage:
    def __init__(self, username, name=None, email=None):
        self.name = name
        self.username = '{}@{}'.format(username, '1786412030005809.onaliyun.com')
        self.email = email
        self.client = self.create_client(ali_setting['akid'], ali_setting['akkey'])

    def create_client(
        self,
        access_key_id: str,
        access_key_secret: str,
    ) -> Ims20190815Client:
        """
        https://next.api.aliyun.com/api/Ims/2019-08-15/CreateUser
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            # 您的AccessKey ID,
            access_key_id=access_key_id,
            # 您的AccessKey Secret,
            access_key_secret=access_key_secret
        )
        # 访问的域名
        config.endpoint = ali_setting['api_url']
        return Ims20190815Client(config)
    
    def get_user(self):
        try:
            get_user_request = ims_20190815_models.GetUserRequest(
                user_principal_name = self.username
            )
            # 复制代码运行请自行打印 API 的返回值
            return_info = self.client.get_user(get_user_request)
            print(return_info)
        except Exception:
            return False
#            traceback.print_exc()
        return True

    def create_user(self):
        create_user_request = ims_20190815_models.CreateUserRequest(
            user_principal_name = self.username,
            display_name = self.name
        )
        return_info = self.client.create_user(create_user_request)
#        print(return_info)
        return True

    def create_login_setting(self):
        passwd = get_passwd()
        self.passwd = passwd
        create_login_profile_request = ims_20190815_models.CreateLoginProfileRequest(
            user_principal_name = self.username,
            password = passwd
        )
        # 复制代码运行请自行打印 API 的返回值
        return_info = self.client.create_login_profile(create_login_profile_request)
#        print(return_info)
        print('ali create_user: ', True)
        print('ali username: {}'.format(self.username))
        print('ali password: {}'.format(self.passwd))
        return True
    
    def update_login_setting(self):
        passwd = get_passwd()
        self.passwd = passwd
        create_login_profile_request = ims_20190815_models.CreateLoginProfileRequest(
            user_principal_name = self.username,
            password = passwd
        )
        # 复制代码运行请自行打印 API 的返回值
        return_info = self.client.update_login_profile(create_login_profile_request)
        print(return_info)
        print('ali username: {}'.format(self.username))
        print('ali password: {}'.format(self.passwd))
        return True

    def delete_user(self):
        delete_user_request = ims_20190815_models.DeleteUserRequest(
            user_principal_name = self.username
        )
        # 复制代码运行请自行打印 API 的返回值
        return_info = self.client.delete_user(delete_user_request)
        return return_info
    def write_file(self, filename):
        with open(filename, 'a') as fd:
            fd.write('dms or ali login url: {}\n'.format(ali_setting['login_url']))
            fd.write('ali user: {}\n'.format(self.username))
            fd.write('ali password: {}\n'.format(self.passwd))
            fd.write('----------\n')


def create_user():
    gituser = gitUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
    aliuser = aliUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
    wikiuser = confluenceUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
    status = True
    if argv_data['gituser']:
        if gituser.get_user():
            print("gitlab: {} alreay exist".format(argv_data['username']))
            status = False
    if argv_data['aliuser']:
        if aliuser.get_user():
            print("ali: {} alreay exist".format(argv_data['username']))
            status = False
    if argv_data['wikiuser']:
        if wikiuser.create_connect():
            if wikiuser.get_user():
                print("wiki: {} alreay exist".format(argv_data['username']))
                status = False
        else:
            status = False
    if status:
        if argv_data['gituser']:
            if gituser.create_user():
                gituser.write_file(argv_data['outfile'])
        if argv_data['aliuser']:
            if aliuser.create_user() and aliuser.create_login_setting():
                aliuser.write_file(argv_data['outfile'])
        if argv_data['wikiuser']:
            if wikiuser.create_user():
                wikiuser.write_file(argv_data['outfile'])
    wikiuser.close()


def reset_passwd():
    # just for aliuser
    if argv_data['aliuser']:
        aliuser = aliUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
        if aliuser.update_login_setting():
            aliuser.write_file(argv_data['outfile'])

def delete_user():
    if argv_data['gituser']:
        gituser = gitUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
        if gituser.get_user():
            print(gituser.delete_user())
        else:
            print('{} not exist'.format(gituser.username))
    if argv_data['aliuser']:
        aliuser = aliUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
        if aliuser.get_user():
            print(aliuser.delete_user())
        else:
            print('{} not exist'.format(aliuser.username))
    if argv_data['wikiuser']:
        wikiuser = confluenceUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
        if wikiuser.create_connect():
            if wikiuser.get_user():
                print(wikiuser.delete_user())
            else:
                print('{} not exist'.format(wikiuser.username))
        else:
            print('wiki server connect fail')
        wikiuser.close()

def offline_user():
    if argv_data['gituser']:
        gituser = gitUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
        if gituser.get_user():
            gituser.block_user()
        else:
            print('{} not exist'.format(gituser.username))
    if argv_data['aliuser']:
        aliuser = aliUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
        if aliuser.get_user():
            print(aliuser.delete_user())
        else:
            print('{} not exist'.format(aliuser.username))
    if argv_data['wikiuser']:
        wikiuser = confluenceUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
        if wikiuser.create_connect():
            if wikiuser.get_user():
                print(wikiuser.deactivate_user())
        else:
            print('{} not exist'.format(wikiuser.username))
        wikiuser.close()

def disable_user():
    # for git user
    if argv_data['gituser']:
        gituser = gitUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
        if gituser.get_user():
            gituser.block_user()
        else:
            print('{} not exist'.format(gituser.username))
    if argv_data['wikiuser']:
        wikiuser = confluenceUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
        if wikiuser.create_connect():
            if wikiuser.get_user():
                print(wikiuser.deactivate_user())
        else:
            print('{} not exist'.format(wikiuser.username))
        wikiuser.close()

def enable_user():
    # for git user
    if argv_data['gituser']:
        gituser = gitUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
        if gituser.get_user():
            gituser.unblock_user()
        else:
            print('{} not exist'.format(gituser.username))
    if argv_data['wikiuser']:
        wikiuser = confluenceUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
        if wikiuser.create_connect():
            if wikiuser.get_user():
                print(wikiuser.reactivate_user())
        else:
            print('{} not exist'.format(wikiuser.username))
        wikiuser.close()

if __name__ == "__main__":
    if argv_data['otype'] == 'create':
        create_user()
    elif argv_data['otype'] == 'offline':
        offline_user()
    elif argv_data['otype'] == 'delete':
        delete_user()
    elif argv_data['otype'] == 'enable':
        enable_user()
    elif argv_data['otype'] == 'disable':
        disable_user()
    elif argv_data['otype'] == 'resetpd':
        reset_passwd()
    else:
        print('create|offline|delete|enable|disable|resetpd')

#wiki_user = confluenceUserManage('test1')
#print(wiki_user.get_user())
#wiki_user.close()

#gituser = gitUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
#gituser.block_user()
#if argv_data['otype'] == 'create':
#    create_user()

#aliuser = aliUserManage(argv_data['username'], argv_data['name'], argv_data['email'])
#return_code = aliuser.get_user()
#print(return_code)

