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
from gui.shared import g_eventBus
from gui.shared import events
from helpers import getShortClientVersion, getClientLanguage

FileServerConf = 'https://bitbucket.org/underph71/all_updaters/raw/main/Shokerix_updater.json'

__version__ = "0.0.1" 
__author__ = "Under_Pressure"
__copyright__ = "Copyright 2025, Under_Pressure"
__mod_name__ = "Updater"


DEBUG_MODE = False
FORCE_LANGUAGE = None 
avc_messagesShown = False

def print_log(log):
    print("[ModPack]: {}".format(str(log)))

def print_error(log):
    print("[ModPack] [ERROR]: {}".format(str(log)))

def print_debug(log):
    global DEBUG_MODE
    if DEBUG_MODE:
        print("[ModPack] [DEBUG]: {}".format(str(log)))

def getLanguage():
    if FORCE_LANGUAGE:
        print_debug('Forced language: {}'.format(FORCE_LANGUAGE))
        return FORCE_LANGUAGE
    
    lang = getClientLanguage()
    print_debug('Auto-detected language: {}'.format(lang))
    return lang

class Data(object):

    def __init__(self):
        self.l_cfg = self.local_conf()
        self.s_cfg = self.server_conf()
        self.messageRepeat = True
        print_debug('install {}'.format(self.l_cfg['LocalVer'] if self.l_cfg else 'Unknown'))

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
            print_debug('Local config loaded successfully')
            return config
        except Exception as Error:
            print_error('Error local cfg: {}'.format(Error))
            return None

    def server_conf(self):
        try:
            context = ssl._create_unverified_context()
            response = urlopen(FileServerConf, context=context)
            fileopen = response.read()
            if hasattr(fileopen, 'decode'):
                fileopen = fileopen.decode('utf-8-sig')
            config = loads(self.comments(fileopen))
            print_debug('Server config loaded successfully')
            return config
        except Exception as Error:
            print_error('Error server cfg: {}'.format(Error))
            return None

    def get_localized_messages(self, message_type):
        if not self.s_cfg or 'SystemMessages' not in self.s_cfg:
            print_debug('No server config or SystemMessages section')
            return None
            
        lang = getLanguage()
        print_debug('Getting messages for language: {}'.format(lang))
        
        lang_map = {
            'uk': 'uk',
            'ru': 'ru',
            'en': 'en',
        }
        
        mapped_lang = lang_map.get(lang, 'en')
        print_debug('Mapped language: {} -> {}'.format(lang, mapped_lang))
        
        sys_messages = self.s_cfg['SystemMessages']
        
        message_key = message_type + '_' + mapped_lang
        print_debug('Looking for message key: {}'.format(message_key))
        
        if message_key in sys_messages:
            print_debug('Found localized messages for: {}'.format(message_key))
            return sys_messages[message_key]
            
        if message_type in sys_messages:
            print_debug('Using fallback messages for: {}'.format(message_type))
            return sys_messages[message_type]
            
        print_debug('No messages found for: {}'.format(message_type))
        return None

def MiniClientVersion():
    try:
        from ResMgr import openSection
        version = openSection('../version.xml')['version'].asString
        return version.split('v.')[1].split(' ')[0]
    except Exception as e:
        print_error('Error getting client version: {}'.format(e))
        return getShortClientVersion().replace('v.', '').strip()

def handleLobbyViewLoaded(_):
    global avc_messagesShown
    
    if avc_messagesShown:
        print_debug('Messages already shown, skipping')
        return
    
    print_debug('Lobby view loaded - processing messages')

    try:
        if not data.l_cfg:
            print_debug('No local config, skipping')
            return
            
        if not data.s_cfg:
            print_debug('No server config, showing error message')
            lang = getLanguage()
            if lang == 'uk':
                error_msg = '<font color="#FF0000" size="15">ModPack</font><br><font color="#dbd7d2" size="13">Не вдається перевірити оновлення</font>'
            elif lang == 'ru':
                error_msg = '<font color="#FF0000" size="15">ModPack</font><br><font color="#dbd7d2" size="13">Не удается проверить обновления</font>'
            else:
                error_msg = '<font color="#FF0000" size="15">ModPack</font><br><font color="#dbd7d2" size="13">Unable to check for updates</font>'
            
            pushMessage(error_msg, SM_TYPE.Warning)
            avc_messagesShown = True
            return
            
        macros = {
            'ServerVer': data.s_cfg.get('ServerVer', ''),
            'LocalVer': data.l_cfg.get('LocalVer', ''),
            'Author': data.s_cfg.get('Author', '')
        }

        print_debug('Using macros: {}'.format(macros))

        local_ver = data.l_cfg.get('LocalVer', '')
        server_ver = data.s_cfg.get('ServerVer', '')

        print_debug('Version comparison: local={}, server={}'.format(local_ver, server_ver))

        if local_ver == server_ver:
            print_debug('Versions match - showing actual messages')

            actual_msg = data.get_localized_messages('ActualMessages')
            if actual_msg and actual_msg.get('Enabled', False):
                messages = actual_msg.get('Messages', [])
                if messages:
                    txt = ''.join(messages).format(**macros)
                    print_debug('Showing actual message: {}'.format(txt[:100]))
                    pushMessage(txt, SM_TYPE.GameGreeting)
            
            info_msg = data.get_localized_messages('InfoMessages')
            if info_msg and info_msg.get('Enabled', False):
                messages = info_msg.get('Messages', [])
                if messages:
                    txt = ''.join(messages).format(**macros)
                    print_debug('Showing info message: {}'.format(txt[:100]))
                    pushMessage(txt, SM_TYPE.GameGreeting)
                    
        elif local_ver < server_ver:
            print_debug('New version available - showing update messages')
            
            new_msg = data.get_localized_messages('NewMessages')
            if new_msg and new_msg.get('Enabled', False):
                messages = new_msg.get('Messages', [])
                if messages:
                    txt = ''.join(messages).format(**macros)
                    print_debug('Showing new version message: {}'.format(txt[:100]))
                    pushMessage(txt, SM_TYPE.GameGreeting)
        else:
            print_debug('Local version is newer than server version')
        
        avc_messagesShown = True
        print_debug('Message processing completed')
        
    except Exception as e:
        print_error('Error in handleLobbyViewLoaded: {}'.format(e))
        import traceback
        traceback.print_exc()


data = None

def init():
    global data
    print_log('MOD {} START LOADING: v{}'. format(__mod_name__, __version__))
    data = Data()
    g_eventBus.addListener(events.GUICommonEvent.LOBBY_VIEW_LOADED, handleLobbyViewLoaded)

def fini():
    global data
    print_log('MOD {} START FINALIZING'.format(__mod_name__))
    g_eventBus.removeListener(events.GUICommonEvent.LOBBY_VIEW_LOADED, handleLobbyViewLoaded)
    data = None
