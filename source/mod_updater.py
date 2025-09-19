# -*- coding: utf-8 -*-
import re
import codecs
import ssl
from json import loads

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

from BigWorld import callback
from gui.SystemMessages import SM_TYPE
from gui.SystemMessages import pushMessage
from gui.Scaleform.daapi.view.lobby.hangar.Hangar import Hangar
from helpers import getShortClientVersion, getClientLanguage

FileServerConf = 'https://bitbucket.org/underph71/all_updaters/raw/d3ecb8e563400e83b77e33394d7897d96d3bdbdd/Shokerix_updater.json'

FORCE_LANGUAGE = None

def getLanguage():
    if FORCE_LANGUAGE:
        return FORCE_LANGUAGE
    return getClientLanguage()

class Data(object):

    def __init__(self):
        self.l_cfg = self.local_conf()
        self.s_cfg = self.server_conf()
        self.messageRepeat = True
        print('[MRVL] install {}'.format(self.l_cfg['LocalVer'] if self.l_cfg else 'Unknown'))

    def comments(self, string, strip_space=True):
        tokenizer = re.compile(r'"|(/\*)|(\*/)|(//)|\n|\r')
        end_slashes_re = re.compile(r'(\\)*$')
        in_string = False
        in_multi = False
        in_single = False
        new_str = []
        index = 0
        
        for match in re.finditer(tokenizer, string):
            if not (in_multi or in_single):
                tmp = string[index:match.start()]
                if not in_string and strip_space:
                    tmp = re.sub(r'[ \t\n\r]+', '', tmp)
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
            print('[MRVL] Error local cfg: {}'.format(Error))
            return None

    def server_conf(self):
        try:
            context = ssl._create_unverified_context()
            response = urlopen(FileServerConf, context=context)
            fileopen = response.read()
            if hasattr(fileopen, 'decode'):
                fileopen = fileopen.decode('utf-8-sig')
            return loads(self.comments(fileopen))
        except Exception as Error:
            print('[MRVL] Error server cfg: {}'.format(Error))
            return None

    def get_localized_messages(self, message_type):
        if not self.s_cfg or 'SystemMessages' not in self.s_cfg:
            return None
            
        lang = getLanguage()
        
        lang_map = {
            'uk': 'uk',
            'ru': 'ru',
            'en': 'en',
        }
        
        mapped_lang = lang_map.get(lang, 'en')
        
        sys_messages = self.s_cfg['SystemMessages']

        message_key = message_type + '_' + mapped_lang
        if message_key in sys_messages:
            return sys_messages[message_key]
            
        if message_type in sys_messages:
            return sys_messages[message_type]
            
        return None

def MiniClientVersion():
    try:
        from ResMgr import openSection
        version = openSection('../version.xml')['version'].asString
        return version.split('v.')[1].split(' ')[0]
    except Exception as e:
        print('[ModPack] Error getting client version: {}'.format(e))
        return getShortClientVersion().replace('v.', '').strip()

original_onVehicleLoaded = Hangar._Hangar__onVehicleLoaded

def onVehicleLoaded(self):
    try:
        original_onVehicleLoaded(self)
        
        if (data.l_cfg is None or 
            data.s_cfg is None or 
            not data.messageRepeat):
            return

        try:
            current_version = MiniClientVersion()
            server_version = data.s_cfg.get('WotVer', '')
            
            if current_version != server_version:
                print('[MRVL] Version mismatch: current={}, server={} - continuing anyway'.format(
                    current_version, server_version))
        except Exception as e:
            print('[MRVL] Version check error: {} - continuing anyway'.format(e))
        
        Macros = {
            'ServerVer': data.s_cfg.get('ServerVer', ''),
            'LocalVer': data.l_cfg.get('LocalVer', ''),
            'Author': data.s_cfg.get('Author', '')
        }

        local_ver = data.l_cfg.get('LocalVer', '')
        server_ver = data.s_cfg.get('ServerVer', '')
        
        lang = getLanguage()
        
        if local_ver == server_ver:
            sys_messages = data.s_cfg.get('SystemMessages', {})
            
            actual_msg = data.get_localized_messages('ActualMessages')
            if actual_msg and actual_msg.get('Enabled', False):
                messages = actual_msg.get('Messages', [])
                if messages:
                    txt = ''.join(messages).format(**Macros)
                    pushMessage(txt, SM_TYPE.GameGreeting)
            
            info_msg = data.get_localized_messages('InfoMessages')
            if info_msg and info_msg.get('Enabled', False):
                messages = info_msg.get('Messages', [])
                if messages:
                    txt = ''.join(messages).format(**Macros)
                    pushMessage(txt, SM_TYPE.GameGreeting)
                    
        elif local_ver < server_ver:
            sys_messages = data.s_cfg.get('SystemMessages', {})
            
            new_msg = data.get_localized_messages('NewMessages')
            if new_msg and new_msg.get('Enabled', False):
                messages = new_msg.get('Messages', [])
                if messages:
                    txt = ''.join(messages).format(**Macros)
                    pushMessage(txt, SM_TYPE.GameGreeting)

        if not data.s_cfg:
            if lang == 'uk':
                error_message = '<font color="#FF0000" size="15">ModPack</font><br><font color="#dbd7d2" size="13">Не вдається перевірити оновлення</font>'
            elif lang == 'ru':
                error_message = '<font color="#FF0000" size="15">ModPack</font><br><font color="#dbd7d2" size="13">Не удается проверить обновления</font>'
            else:  
                error_message = '<font color="#FF0000" size="15">ModPack</font><br><font color="#dbd7d2" size="13">Unable to check for updates</font>'

            pushMessage(error_message, SM_TYPE.Warning)
        
        data.messageRepeat = False
        
    except Exception as e:
        print('[MRVL] Error in onVehicleLoaded: {}'.format(e))

data = Data()

Hangar._Hangar__onVehicleLoaded = onVehicleLoaded