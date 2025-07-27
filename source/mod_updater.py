import re
import codecs
import ssl
from json import loads

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

from gui.SystemMessages import SM_TYPE
from gui.SystemMessages import pushMessage
from gui.Scaleform.daapi.view.lobby.hangar.Hangar import Hangar
from helpers import getShortClientVersion

FileServerConf = 'https://bitbucket.org/underph71/all_updaters/raw/main/MRVL_updater.json'

class Data(object):

    def __init__(self):
        self.l_cfg = self.local_conf()
        self.s_cfg = self.server_conf()
        self.messageRepeat = True
        print('MRVL install {}'.format(self.l_cfg['LocalVer'] if self.l_cfg else 'Unknown'))

    def comments(self, string, strip_space=True):
        tokenizer = re.compile('"|(/\\*)|(\\*/)|(//)|\n|\r')
        end_slashes_re = re.compile('(\\\\)*$')
        in_string = False
        in_multi = False
        in_single = False
        new_str = []
        index = 0
        
        for match in re.finditer(tokenizer, string):
            if not (in_multi or in_single):
                tmp = string[index:match.start()]
                if not in_string and strip_space:
                    tmp = re.sub('[ \t\n\r]+', '', tmp)
                new_str.append(tmp)
            index = match.end()
            val = match.group()
            
            if val == '"' and not (in_multi or in_single):
                escaped = end_slashes_re.search(string, 0, match.start())
                if not in_string or escaped is None or len(escaped.group()) % 2 == 0:
                    in_string = not in_string
                index -= 1
            elif not (in_string or in_multi or in_single):
                if val == '/*':
                    in_multi = True
                elif val == '//':
                    in_single = True
            elif val == '*/' and in_multi and not (in_string or in_single):
                in_multi = False
            elif val in '\r\n' and not (in_multi or in_string) and in_single:
                in_single = False
            elif not (in_multi or in_single or val in ' \r\n\t' and strip_space):
                new_str.append(val)

        new_str.append(string[index:])
        return ''.join(new_str)

    def local_conf(self):
        try:
            clientVersion = getShortClientVersion().replace('v.', '').strip()
            cfg_file = './mods/configs/updater.json'
            
            with codecs.open(cfg_file, mode='r', encoding='utf-8-sig') as json_file:
                fileopen = json_file.read() 
            return loads(self.comments(fileopen))
        except Exception as Error:
            print('Error local cfg: {}'.format(Error))
            return None

    def server_conf(self):
        try:
            context = ssl._create_unverified_context()
            response = urlopen(FileServerConf, context=context)
            fileopen = response.read().decode('utf-8-sig')
            return loads(self.comments(fileopen))
        except Exception as Error:
            print('Error server cfg: {}'.format(Error))
            return None

def MiniClientVersion():
    try:
        from ResMgr import openSection
        version = openSection('../version.xml')['version'].asString
        return version.split('v.')[1].split(' ')[0]
    except Exception as e:
        print('Error getting client version: {}'.format(e))
        return getShortClientVersion().replace('v.', '').strip()

original_onVehicleLoaded = Hangar._Hangar__onVehicleLoaded

def onVehicleLoaded(self):
    try:
        original_onVehicleLoaded(self)
        
        if (data.l_cfg is None or 
            data.s_cfg is None or 
            not data.messageRepeat):
            return
            
        # Спрощена перевірка версій - не блокуємо роботу при невідповідності
        try:
            current_version = MiniClientVersion()
            server_version = data.s_cfg.get('WotVer', '')
            
            if current_version != server_version:
                print('Version mismatch: current={}, server={} - continuing anyway'.format(current_version, server_version))
                # Не повертаємося, продовжуємо роботу
        except Exception as e:
            print('Version check error: {} - continuing anyway'.format(e))
            # Не повертаємося, продовжуємо роботу
        
        Macros = {
            'ServerVer': data.s_cfg.get('ServerVer', ''),
            'LocalVer': data.l_cfg.get('LocalVer', ''),
            'Author': data.s_cfg.get('Author', '')
        }

        local_ver = data.l_cfg.get('LocalVer', '')
        server_ver = data.s_cfg.get('ServerVer', '')
        
        if local_ver == server_ver:
            sys_messages = data.s_cfg.get('SystemMessages', {})
            
            actual_msg = sys_messages.get('ActualMessages', {})
            if actual_msg.get('Enabled', False):
                messages = actual_msg.get('Messages', [])
                if messages:
                    txt = ''.join(messages).format(**Macros)
                    pushMessage(txt, SM_TYPE.GameGreeting)
                    
            info_msg = sys_messages.get('InfoMessages', {})
            if info_msg.get('Enabled', False):
                messages = info_msg.get('Messages', [])
                if messages:
                    txt = ''.join(messages).format(**Macros)
                    pushMessage(txt, SM_TYPE.GameGreeting)
                    
        elif local_ver < server_ver:
            sys_messages = data.s_cfg.get('SystemMessages', {})
            new_msg = sys_messages.get('NewMessages', {})
            if new_msg.get('Enabled', False):
                messages = new_msg.get('Messages', [])
                if messages:
                    txt = ''.join(messages).format(**Macros)
                    pushMessage(txt, SM_TYPE.GameGreeting)
        
        data.messageRepeat = False
        
    except Exception as e:
        print('Error in onVehicleLoaded: {}'.format(e))

data = Data()

Hangar._Hangar__onVehicleLoaded = onVehicleLoaded
