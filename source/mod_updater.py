import re
from json import loads
from urllib2 import urlopen
from gui.SystemMessages import SM_TYPE
from gui.SystemMessages import pushMessage
from gui.Scaleform.daapi.view.lobby.hangar.Hangar import Hangar
from helpers import getShortClientVersion

FileServerConf = 'https://github.com/UnderPressurePH7/G_UA-mods/releases/download/mods_updater_4/Kudmood_updater_eu.json'

class Data(object):

    def __init__(self):
        self.l_cfg = self.local_conf()
        self.s_cfg = self.server_conf()
        self.messageRepeat = True
        print 'MRVL install {}'.format(self.l_cfg['LocalVer'] if self.l_cfg else 'Unknown')

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
            import codecs
            clientVersion = getShortClientVersion().replace('v.', '').strip()
            cfg_file = './mods/configs/updater.json'
            
            with codecs.open(cfg_file, mode='r', encoding='utf-8-sig') as json_file:
                fileopen = json_file.read().decode('utf-8-sig')
            return loads(self.comments(fileopen))
        except Exception as Error:
            print 'Error local cfg:', Error
            return None

    def server_conf(self):
        try:
            import ssl
            context = ssl._create_unverified_context()
            fileopen = urlopen(FileServerConf, context=context).read().decode('utf-8-sig')
            return loads(self.comments(fileopen))
        except Exception as Error:
            print 'Error server cfg:', Error
            return None

def MiniClientVersion():
    from ResMgr import openSection
    version = openSection('../version.xml')['version'].asString
    return version.split('v.')[1].split(' ')[0]

def onVehicleLoaded(self, base=Hangar._Hangar__onVehicleLoaded):
    base(self)
    
    if (data.l_cfg is not None and 
        data.s_cfg is not None and 
        MiniClientVersion() == data.s_cfg['WotVer'] and 
        data.messageRepeat):
        
        Macros = {
            'ServerVer': data.s_cfg['ServerVer'],
            'LocalVer': data.l_cfg['LocalVer'],
            'Author': data.s_cfg['Author']
        }

        if data.l_cfg['LocalVer'] == data.s_cfg['ServerVer']:
            if data.s_cfg['SystemMessages']['ActualMessages']['Enabled']:
                txt = ''.join(data.s_cfg['SystemMessages']['ActualMessages']['Messages'])
                txt = txt.format(**Macros)
                pushMessage(txt, SM_TYPE.GameGreeting)
                
            if data.s_cfg['SystemMessages']['InfoMessages']['Enabled']:
                txt = ''.join(data.s_cfg['SystemMessages']['InfoMessages']['Messages'])
                txt = txt.format(**Macros)
                pushMessage(txt, SM_TYPE.GameGreeting)
                
        elif data.l_cfg['LocalVer'] < data.s_cfg['ServerVer']:
            if data.s_cfg['SystemMessages']['NewMessages']['Enabled']:
                txt = ''.join(data.s_cfg['SystemMessages']['NewMessages']['Messages'])
                txt = txt.format(**Macros)
                pushMessage(txt, SM_TYPE.GameGreeting)
        
        data.messageRepeat = False

data = Data()

Hangar._Hangar__onVehicleLoaded = onVehicleLoaded