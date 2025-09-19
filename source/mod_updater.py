# -*- coding: utf-8 -*-
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
from helpers import getShortClientVersion, getClientLanguage

FileServerConf = 'https://bitbucket.org/underph71/all_updaters/raw/main/ModPack_updater.json'

FORCE_LANGUAGE = None 

def getLanguage():
    if FORCE_LANGUAGE:
        print('[ModPack] Forced language: {}'.format(FORCE_LANGUAGE))
        return FORCE_LANGUAGE
    
    lang = getClientLanguage()
    print('[ModPack] Auto-detected language: {}'.format(lang))
    return lang

class Data(object):

    def __init__(self):
        self.l_cfg = self.local_conf()
        self.s_cfg = self.server_conf()
        self.messageRepeat = True
        print('[ModPack] install {}'.format(self.l_cfg['LocalVer'] if self.l_cfg else 'Unknown'))

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
            cfg_file = './mods/configs/updater.json'
            with codecs.open(cfg_file, mode='r', encoding='utf-8-sig') as json_file:
                fileopen = json_file.read() 
            config = loads(self.comments(fileopen))
            print('[ModPack] Local config loaded successfully')
            return config
        except Exception as Error:
            print('[ModPack] Error local cfg: {}'.format(Error))
            return None

    def server_conf(self):
        try:
            context = ssl._create_unverified_context()
            response = urlopen(FileServerConf, context=context)
            fileopen = response.read()
            if hasattr(fileopen, 'decode'):
                fileopen = fileopen.decode('utf-8-sig')
            config = loads(self.comments(fileopen))
            print('[ModPack] Server config loaded successfully')
            return config
        except Exception as Error:
            print('[ModPack] Error server cfg: {}'.format(Error))
            return None

    def get_localized_messages(self, message_type):
        if not self.s_cfg or 'SystemMessages' not in self.s_cfg:
            print('[ModPack] No server config or SystemMessages section')
            return None
            
        lang = getLanguage()
        print('[ModPack] Getting messages for language: {}'.format(lang))
        
        lang_map = {
            'uk': 'uk',
            'ru': 'ru',
            'en': 'en',
        }
        
        mapped_lang = lang_map.get(lang, 'en')
        print('[ModPack] Mapped language: {} -> {}'.format(lang, mapped_lang))
        
        sys_messages = self.s_cfg['SystemMessages']
        
        message_key = message_type + '_' + mapped_lang
        print('[ModPack] Looking for message key: {}'.format(message_key))
        
        if message_key in sys_messages:
            print('[ModPack] Found localized messages for: {}'.format(message_key))
            return sys_messages[message_key]
            
        if message_type in sys_messages:
            print('[ModPack] Using fallback messages for: {}'.format(message_type))
            return sys_messages[message_type]
            
        print('[ModPack] No messages found for: {}'.format(message_type))
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
    print('[ModPack] onVehicleLoaded called')

    try:
        original_onVehicleLoaded(self)
        print('[ModPack] Original onVehicleLoaded completed')
        
        if not hasattr(data, 'messageRepeat') or not data.messageRepeat:
            print('[ModPack] Messages already shown, skipping')
            return
            
        if not data.l_cfg:
            print('[ModPack] No local config, skipping')
            return
            
        if not data.s_cfg:
            print('[ModPack] No server config, showing error message')
            lang = getLanguage()
            if lang in ['uk', 'ua']:
                error_msg = '<font color="#FF0000" size="15">ModPack</font><br><font color="#dbd7d2" size="13">Не вдається перевірити оновлення</font>'
            elif lang == 'ru':
                error_msg = '<font color="#FF0000" size="15">ModPack</font><br><font color="#dbd7d2" size="13">Не удається перевірити оновлення</font>'
            elif lang == 'ru':
                error_msg = '<font color="#FF0000" size="15">ModPack</font><br><font color="#dbd7d2" size="13">Не удається перевірити оновлення</font>'
            else:
                error_msg = '<font color="#FF0000" size="15">ModPack</font><br><font color="#dbd7d2" size="13">Unable to check for updates</font>'
            
            pushMessage(error_msg, SM_TYPE.Warning)
            data.messageRepeat = False
            return
            
        macros = {
            'ServerVer': data.s_cfg.get('ServerVer', ''),
            'LocalVer': data.l_cfg.get('LocalVer', ''),
            'Author': data.s_cfg.get('Author', '')
        }

        print('[ModPack] Using macros: {}'.format(macros))

        local_ver = data.l_cfg.get('LocalVer', '')
        server_ver = data.s_cfg.get('ServerVer', '')

        print('[ModPack] Version comparison: local={}, server={}'.format(local_ver, server_ver))

        if local_ver == server_ver:

            print('[ModPack] Versions match - showing actual messages')

            actual_msg = data.get_localized_messages('ActualMessages')
            if actual_msg and actual_msg.get('Enabled', False):
                messages = actual_msg.get('Messages', [])
                if messages:
                    txt = ''.join(messages).format(**macros)
                    print('[ModPack] Showing actual message: {}'.format(txt[:100]))
                    pushMessage(txt, SM_TYPE.GameGreeting)
            
            info_msg = data.get_localized_messages('InfoMessages')
            if info_msg and info_msg.get('Enabled', False):
                messages = info_msg.get('Messages', [])
                if messages:
                    txt = ''.join(messages).format(**macros)
                    print('[ModPack] Showing info message: {}'.format(txt[:100]))
                    pushMessage(txt, SM_TYPE.GameGreeting)
                    
        elif local_ver < server_ver:
            print('[ModPack] New version available - showing update messages')
            
            new_msg = data.get_localized_messages('NewMessages')
            if new_msg and new_msg.get('Enabled', False):
                messages = new_msg.get('Messages', [])
                if messages:
                    txt = ''.join(messages).format(**macros)
                    print('[ModPack] Showing new version message: {}'.format(txt[:100]))
                    pushMessage(txt, SM_TYPE.GameGreeting)
        else:
            print('[ModPack] Local version is newer than server version')
        
        data.messageRepeat = False
        print('[ModPack] Message processing completed')
        
    except Exception as e:
        print('[ModPack] Error in onVehicleLoaded: {}'.format(e))
        import traceback
        traceback.print_exc()


print('[ModPack] Initializing mod...')
data = Data()

print('[ModPack] Patching Hangar._Hangar__onVehicleLoaded')
Hangar._Hangar__onVehicleLoaded = onVehicleLoaded

print('[ModPack] Mod initialization completed')