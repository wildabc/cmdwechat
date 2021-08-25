from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

import threading
import time
import itchat

def timestr():
    return time.strftime('%H:%M')

@itchat.msg_register('Text')
def receive_msg(msg):
    "monitor new message to call this function"
    # get message content
    content = msg['Text']
    # get message sender
    if "RemarkName" in msg['User']:
        friend_name = msg['User']['RemarkName'] or msg['User']['NickName']
    else:
        friend_name = msg['User']['UserName']
    if friend_name == 'filehelper': friend_name = '文件传输助手'
    # show received message
    if msg['FromUserName'] == msg['User']['UserName']:
        text = FormattedText([
                ('bg:#4D4D4D', content),
                ('', f' ({timestr()}<-{friend_name})')
            ])
    # show sent message
    else:
        text = FormattedText([
                ('bg:#2BA245', content),
                ('', f' ({timestr()}->{friend_name})')
            ])
    print_formatted_text(text)

@itchat.msg_register(['Picture', 'Recording', 'Attachment', 'Video'])
def download_files(msg):
    # download it
    content = msg['FileName']
    msg.download(content)
    # get message time
    time_ = timestr()
    # get message sender
    if "RemarkName" in msg['User']:
        friend_name = msg['User']['RemarkName'] or msg['User']['NickName']
    else:
        friend_name = msg['User']['UserName']
    if friend_name == 'filehelper': friend_name = '文件传输助手'
    if msg['Type'] == 'Picture':
        prefix = '@img@'
    elif msg['Type'] == 'Video':
        prefix = '@vid@'
    else:
        prefix = '@fil@'
    # show received message
    if msg['FromUserName'] == msg['User']['UserName']:
        text = FormattedText([
            ('bg:#4D4D4D', prefix+content),
            ('', f' ({timestr()}<-{friend_name})')
        ])
    # show sent message
    else:
        text = FormattedText([
            ('bg:#2BA245', prefix+content),
            ('', f' ({timestr()}->{friend_name})')
        ])
    print_formatted_text(text)

class Client:
    def __init__(self):
        self.update()
        self.to = '文件传输助手'

    def update(self):
        frienddict = {'文件传输助手': 'filehelper'}

        friends = itchat.get_friends(update=True)
        for f in friends:
            name = f['RemarkName'] or f['NickName']
            id = f['UserName']
            frienddict[name] = id

        self.completer = NestedCompleter.from_nested_dict({
            '_to': set(frienddict.keys()),
            '_exit': None,
            '_update': None
        })
        self.frienddict = frienddict

    def send(self, content):
        id = self.frienddict[self.to]
        res = itchat.send(content, toUserName=id)
        if res['BaseResponse']['Ret'] != 0:
            print('发送失败！')
            return
        text = FormattedText([
            ('bg:#2BA245', content),
            ('', f' ({timestr()}->{self.to})')
        ])
        print_formatted_text(text)

    def cmdloop(self):
        session = PromptSession()
        while True:
            line = session.prompt(self.to+'>', completer=self.completer)
            line = line.strip()
            if line == '':
                continue
            elif line == '_exit':
                return
            elif line == '_update':
                self.update()
            elif line.startswith('_to '):
                name = line.lstrip('_to ')
                if name in self.frienddict.keys():
                    self.to = name
                else:
                    print('无此好友')
            else:
                self.send(line)

if __name__ == '__main__':
    itchat.auto_login(hotReload=True)
    with patch_stdout():
        threading.Thread(target=itchat.run, daemon=True).start()
        threading.Thread(target=Client().cmdloop).start()