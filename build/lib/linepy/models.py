# -*- coding: utf-8 -*-
from datetime import datetime
from random import randint

import json, shutil, tempfile, time

def loggedIn(func):
    def checkLogin(*args, **kwargs):
        if args[0].isLogin:
            return func(*args, **kwargs)
        else:
            args[0].callback.other("You must login to LINE")
    return checkLogin
    
class LineModels(object):
        
    """Text"""
    def __init__(self):
        if self.isLogin == True:
            self.log("[%s] : Login success" % self.profile.displayName)

    def log(self, text):
        print("[%s] %s" % (str(datetime.now()), text))

    """Personalize"""
    
    @loggedIn
    def cloneContactProfile(self, mid):
        contact = self.getContact(mid)
        profile = self.profile
        profile.displayName = contact.displayName
        profile.statusMessage = contact.statusMessage
        profile.pictureStatus = contact.pictureStatus
        self.updateProfileAttribute(8, profile.pictureStatus)
        return self.updateProfile(profile)

    @loggedIn
    def updateProfilePicture(self, path):
        file=open(path, 'rb')
        files = {
            'file': file
        }
        params = {
            'name': 'media',
            'type': 'image',
            'oid': self.profile.mid,
            'ver': '1.0',
        }
        data={
            'params': json.dumps(params)
        }
        r = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/talk/p/upload.nhn', data=data, files=files)
        if r.status_code != 201:
            raise Exception('Update profile picture failure.')
        return True

    # It's still development, if you have a working code please pull it on linepy GitHub Repo
    @loggedIn
    def updateProfileCover(self, path):
        if len(self.server.channelHeaders) < 1:
            raise Exception('LineChannel is required for acquire this action.')
        else:
            headers, optionsHeaders={}, {}
            optionsHeaders.update(self.server.channelHeaders)
            optionsHeaders.update({
                'access-control-request-headers': 'content-type,x-obs-params,x-obs-userdata,X-Line-ChannelToken',
                'access-control-request-method': 'POST'
            })
            opt_r = self.server.optionsContent(self.server.LINE_OBS_DOMAIN + '/myhome/c/upload.nhn', headers=optionsHeaders)
            if opt_r.status_code == 200:
                headers.update(self.server.channelHeaders)
                self.server.setChannelHeaders('Content-Type', 'image/jpeg')
                file=open(path, 'rb')
                files = {
                    'file': file
                }
                params = {
                    'name': 'media',
                    'type': 'image',
                    'userid': self.profile.mid,
                    'ver': '1.0',
                }
                data={
                    'params': json.dumps(params)
                }
                r = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/myhome/c/upload.nhn', data=data, files=files)
                if r.status_code != 201:
                    raise Exception('Update profile cover failure.')
                return True
            else:
                raise Exception('Cannot set options headers.')

    """Object"""

    def downloadFileURL(self, fileUrl, returnAs='path', saveAs=''):
        if returnAs not in ['path','bool','bin']:
            raise Exception('Invalid returnAs value')
        if saveAs == '':
            saveAs = '%s/linepy-%i-%i.bin' % (tempfile.gettempdir(), randint(0, 9), int(time.time()))
        r = self.server.getContent(fileUrl)
        if r.status_code == 200:
            if returnAs in ['path','bool']:
                with open(saveAs, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                if returnAs == 'path':
                    return saveAs
                elif returnAs == 'bool':
                    return True
            elif returnAs == 'bin':
                return r.raw
        else:
            raise Exception('Download file failure.')

    @loggedIn
    def downloadObjectMsg(self, path, messageId, returnAs='path', saveAs=''):
        if saveAs == '':
            saveAs = '%s/linepy-%s-%i-%i.bin' % (tempfile.gettempdir(), messageId, randint(0, 9), int(time.time()))
        if returnAs not in ['path','bool','bin']:
            raise Exception('Invalid returnAs value')
        params = {'oid': messageId}
        url = self.server.urlEncode(self.server.LINE_OBS_DOMAIN, '/talk/m/download.nhn', params)
        r = self.server.getContent(url)
        if r.status_code == 200:
            if returnAs in ['path','bool']:
                with open(saveAs, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                if returnAs == 'path':
                    return saveAs
                elif returnAs == 'bool':
                    return True
            elif returnAs == 'bin':
                return r.raw
        else:
            raise Exception('Download object failure.')

    @loggedIn
    def forwardObjectMsg(self, to, msgId, contentType='image'):
        if contentType not in ['image','video','audio']:
            raise Exception('Type not valid.')
        data = {
            'name': 'media',
            'oid': 'reqseq',
            'reqseq': self.revision,
            'type': contentType,
            'tomid': to,
            'copyFrom': '/talk/m/%s' % msgId,
            'ver': '1.0',
        }
        r = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/talk/m/copy.nhn', data=data)
        if r.status_code != 200:
            raise Exception('Forward object failure.')
        return True
        
    @loggedIn
    def sendImage(self, to, path):
        objectId = self.sendMessage(to=to, text=None, contentType = 1).id
        files = {
            'file': open(path, 'rb'),
        }
        params = {
            'name': 'media',
            'oid': objectId,
            'size': len(open(path, 'rb').read()),
            'type': 'image',
            'ver': '1.0',
        }
        data = {
            'params': json.dumps(params)
        }
        r = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/talk/m/upload.nhn', data=data, files=files)
        if r.status_code != 201:
            raise Exception('Upload image failure.')
        return True

    @loggedIn
    def sendImageWithURL(self, to, url):
        path = self.downloadFileURL(url, 'path')
        return self.sendImage(to, path)

    @loggedIn
    def sendVideo(self, to, path):
        contentMetadata = {
            'VIDLEN' : '60000',
            'DURATION' : '60000'
        }
        objectId = self.sendMessage(to=to, text=None, contentMetadata=contentMetadata, contentType = 2).id
        files = {
            'file': open(path, 'rb')
        }
        params = {
            'name': 'media',
            'oid': objectId,
            'size': len(open(path, 'rb').read()),
            'type': 'video',
            'ver': '1.0',
        }
        data = {
            'params': json.dumps(params)
        }
        r = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/talk/m/upload.nhn', data=data, files=files)
        if r.status_code != 201:
            raise Exception('Upload video failure.')
        return True

    @loggedIn
    def sendVideoWithURL(self, to, url):
        path = self.downloadFileURL(url, 'path')
        return self.sendVideo(to, path)

    @loggedIn
    def sendAudio(self, to, path):
        objectId = self.sendMessage(to=to, text=None, contentType = 3).id
        files = {
            'file': open(path, 'rb'),
        }
        params = {
            'name': 'media',
            'oid': objectId,
            'size': len(open(path, 'rb').read()),
            'type': 'audio',
            'ver': '1.0',
        }
        data = {
            'params': json.dumps(params)
        }
        r = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/talk/m/upload.nhn', data=data, files=files)
        if r.status_code != 201:
            raise Exception('Upload audio failure.')
        return True

    @loggedIn
    def sendAudioWithURL(self, to, url):
        path = self.downloadFileURL(url, 'path')
        return self.sendAudio(to, path)

    @loggedIn
    def sendFile(self, to, path, file_name=''):
        if file_name == '':
            import ntpath
            file_name = ntpath.basename(path)
        file_size = len(open(path, 'rb').read())
        contentMetadata = {
            'FILE_NAME' : str(file_name),
            'FILE_SIZE' : str(file_size)
        }
        objectId = self.sendMessage(to=to, text=None, contentMetadata=contentMetadata, contentType = 14).id
        files = {
            'file': open(path, 'rb'),
        }
        params = {
            'name': file_name,
            'oid': objectId,
            'size': file_size,
            'type': 'file',
            'ver': '1.0',
        }
        data = {
            'params': json.dumps(params)
        }
        r = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/talk/m/upload.nhn', data=data, files=files)
        if r.status_code != 201:
            raise Exception('Upload file failure.')
        return True

    @loggedIn
    def sendFileWithURL(self, to, url, fileName=''):
        path = self.downloadFileURL(url, 'path')
        return self.sendFile(to, path, fileName)