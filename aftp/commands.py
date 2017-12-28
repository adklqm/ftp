#conding:utf-8
import  sublime,sublime_plugin
import  os
from    .filetransfer import FileTransfer as FTP
import  json
from    ..AFTP import DEFAULT_CONFIG,DEFAULT_CONFIG_PATH
import  threading

#Instance of AFTP
AFTP         = False
#It is a path for aftp-config.json
LOCAL_PATH   = False
# A json object for AFTP
AFTP_CONFIG  = False

# Get a AFTP object
def getAftp(path):
    global AFTP
    global LOCAL_PATH
    global AFTP_CONFIG

    log_panel = sublime.active_window().find_output_panel('aftp')

    tmp = getLocalPath(path)
    if False == tmp:
        LOCAL_PATH  = False
        AFTP_CONFIG  = False
        if False != AFTP:
            AFTP.close()
            AFTP = False
        log_panel.run_command('append',{"characters":"Load configuration file failed\n"})
        return

    if tmp != LOCAL_PATH:
        LOCAL_PATH = tmp
        AFTP_CONFIG = False
        if False != AFTP:
            AFTP.close()
            AFTP = False

    config = getConfig(LOCAL_PATH)
    if False == config:
        LOCAL_PATH = False
        AFTP_CONFIG = False
        if False != AFTP:
            AFTP.close()
            AFTP = False
        log_panel.run_command('append',{"characters":"Load configuration file failed\n"})
        return

    config['local_path'] = LOCAL_PATH

    if False == AFTP_CONFIG:
        AFTP_CONFIG = config
    elif (config == AFTP_CONFIG):
        pass
    else:
        tmp_conf = AFTP_CONFIG
        AFTP_CONFIG = config
        if (tmp_conf['host'] != config['host'] or tmp_conf['user'] != config['user']
             or tmp_conf['password'] != config['password'] or tmp_conf['ftp_passive_mode'] != config['ftp_passive_mode']):
            if False != AFTP:
                AFTP.close()
                AFTP = False

    # Check AFTP isn't valid
    if False != AFTP:
        if True == AFTP.checkConnect():
            pass
        else:
            log_panel.run_command('append',{"characters":"Connect is disable\n"})
            AFTP = False

    if False == AFTP:
        try:
            msg = 'Connecting to FTP server '+config['host']+' as '+config['user']+'......................'
            log_panel.run_command('append',{"characters":msg})
            AFTP = FTP(config)
            AFTP.Login()
            log_panel.run_command('append',{"characters":"success\n"})
        except Exception:
            AFTP = False
            log_panel.run_command('append',{"characters":"\nConnection timed out\n"})

# Load config content
def getConfig(localDir):
    try:
        fp     = open(os.path.join(localDir,'aftp-config.json') ,'r',encoding = 'utf-8')
    except Exception:
        return False
    try:
        config = json.load(fp)
        return config
    except Exception:
        return False

# Get path for local directory
def getLocalPath(path):
    fileDir = (os.path.split(path))[0]
    tmp     = ''

    for x in os.listdir(fileDir):
        tmp = os.path.join(fileDir,x)
        if( os.path.isfile(tmp) and "aftp-config.json" == x ):
            return fileDir

    if(len(fileDir) < 4):
        return False
    return getLocalPath(fileDir)

# Get path for remote directory
def getRemotePath(localDir,path):
    config = getConfig(localDir)
    if False == config:
        return False
    try:
        remotePath = config['remote_path']
    except Exception:
        sublime.active_window().find_output_panel('aftp').run_command('append',{"characters":"Failed get remote_path from config file\n"})
        return False
    #If it doesn't end with "/"
    if remotePath[-1] != "/":
        remotePath = remotePath + "/"

    tmp = path.replace(localDir + "\\",'')
    tmp = tmp.replace("\\","/")
    remotePath  = remotePath + tmp
    return remotePath

# Check command is valid
def valid(**args):
    config_path = getLocalPath(args['path'])
    if False == config_path:
        if 'transfer' == args['action']:
            return False
        elif 'config' == args['action']:
            if os.path.isdir(args['path']):
                if os.path.isfile( os.path.join(args['path'],'aftp-config.json') ):
                    return False
            return True
        else:
            return False

    else:
        if 'config' == args['action']:
            return False
        else:
            pass

    if 'transfer' == args['action']:
        if 'file' == args['command_type']:
            if os.path.isdir(args['path']):
                return False
            else:
                return True
        elif 'folder' == args['command_type']:
            if os.path.isdir(args['path']):
                return True
            else:
                return False
        else:
            return False
    else:
        return False

# Execute a command
def executeCommand(command,path):
    global AFTP
    global LOCAL_PATH

    active_window = sublime.active_window()
    log_panel     = active_window.find_output_panel('aftp')
    if None == log_panel:
        log_panel     = active_window.create_output_panel('aftp')

    active_window.run_command('show_panel',{"panel":"output.aftp"})
    localDir = getLocalPath(path)
    config   = getConfig(localDir)
    if False == config:
        log_panel.run_command('append',{"characters":"Failed to load config\n"})
        return False

    getAftp(path)
    if False == AFTP:
        return

    remote_path = getRemotePath(LOCAL_PATH,path)
    try:
        if 'AftpUploadFile' == command:
            try:
                ignore = config['ignore']
                if os.path.split(path)[1] in ignore:
                    return
            except Exception:
                pass
            msg = 'Uploading remote file:'+remote_path+'....................................'
            log_panel.run_command('append',{"characters":msg})
            AFTP.UploadFile(path,remote_path)

        if 'AftpDownloadFile' == command:
            msg = 'Downloading remote file:'+remote_path+'....................................'
            log_panel.run_command('append',{"characters":msg})
            AFTP.UploadFile(path,remote_path)

        if 'AftpDeleteRemoteFile' == command:
            msg = 'Deleting remote file'+remote_path+'.......................................'
            log_panel.run_command('append',{"characters":msg})
            AFTP.DeleteRemoteFile(path,remote_path)

        if 'AftpUploadFolder' == command:
            try:
                ignore = config['ignore']
            except:
                ignore = []
                pass
            for ignore_file in ignore:
                if -1 != ignore_file.find('/'):
                    if ignore_file[-1] != '/':
                        ignore_file = ignore_file + '/'

                    ignore_file = ignore_file.replace("/",os.path.sep)
                    if os.path.join(LOCAL_PATH,ignore_file) == path + os.path.sep:
                        return
            msg = 'Uploading remote folder:'+remote_path+'....................................'
            log_panel.run_command('append',{"characters":msg})
            AFTP.UploadFolder(path,remote_path)

        if 'AftpDownloadFolder' == command:
            msg = 'Downloading remote folder:'+remote_path+'....................................'
            log_panel.run_command('append',{"characters":msg})
            AFTP.DownloadFolder(path,remote_path)

        if 'AftpDeleteRemoteFolder' == command:
            msg = 'Deleting remote folder'+remote_path+'....................................'
            log_panel.run_command('append',{"characters":msg})
            AFTP.DeleteRemoteFolder(path,remote_path)

        if 'AftpDiffRemoteFile' == command:
             msg = 'Comparing remote file:'+remote_path+'....................................'
             log_panel.run_command('append',{"characters":msg})
             AFTP.DiffRemoteFile(path,remote_path)

        log_panel.run_command('append',{"characters":'success\n'})

    except Exception:
        if 'AftpUploadFile' == command:
            msg = '\nFailed to upload local file\n'
        if 'AftpDeleteRemoteFile'   == command:
            msg = '\nFailed to delete remote file\n'
        if 'AftpUploadFolder'       == command:
            msg = '\nFailed to upload local folder\n'
        if 'AftpDownloadFolder'     == command:
            msg = '\nFailed to download remote folder\n'
        if 'AftpDeleteRemoteFolder' == command:
            msg = '\nFailed to delete remote folder\n'
        if 'AftpDiffRemoteFile'     == command:
            msg = '\nFailed to compare remote file\n'
        log_panel.run_command('append',{"characters":msg})

# A command that upload file to remote server
class AftpUploadFileCommand(sublime_plugin.TextCommand):

    def run(self,edit,**args):
        try:
            path = args['paths'][0]
        except Exception:
            path = self.view.file_name()

        t = threading.Thread(target = executeCommand,args=('AftpUploadFile',path,))
        t.start()

    # Command is enabled
    def is_enabled(self,**args):
        return AftpUploadFileCommand._check(self,**args)

    # Command is visible
    def is_visible(self,**args):
        return AftpUploadFileCommand._check(self,**args)

    # Check command is valid
    def _check(self,**args):
        try:
            path = args['paths'][0]
        except Exception:
            path = self.view.file_name()

        paragrams = {}
        paragrams['path']   = path
        paragrams['command_type']   = 'file'
        paragrams['action'] = 'transfer'

        return valid(**paragrams)

# A command that download file from remote server
class AftpDownloadFileCommand(sublime_plugin.TextCommand):
    def run(self,edit,**args):
        try:
            path = args['paths'][0]
        except Exception:
            path = self.view.file_name()

        t = threading.Thread(target = executeCommand,args=('AftpDownloadFile',path,))
        t.start()

    # Command is enabled
    def is_enabled(self,**args):
        return AftpDownloadFileCommand._check(self,**args)

    # Command is visible
    def is_visible(self,**args):
        return AftpDownloadFileCommand._check(self,**args)

    # Check command is valid
    def _check(self,**args):
        try:
            path = args['paths'][0]
        except Exception:
            path = self.view.file_name()

        paragrams = {}
        paragrams['path']   = path
        paragrams['command_type']   = 'file'
        paragrams['action'] = 'transfer'

        return valid(**paragrams)

# A command that delete file from remote server
class AftpDeleteRemoteFileCommand(sublime_plugin.TextCommand):
    def run(self,edit,**args):
        try:
            path = args['paths'][0]
        except Exception:
            path = self.view.file_name()

        localDir = getLocalPath(path)
        if False == localDir:
            return False
        file_name = getRemotePath(localDir,path)
        if False == file_name:
            return False

        result = sublime.ok_cancel_dialog('Confirm delete remote file: \n'+file_name,'ok')
        if False == result:
            return False
        t = threading.Thread(target = executeCommand,args=('AftpDeleteRemoteFile',path,))
        t.start()

    def is_enabled(self,**args):
        return AftpDeleteRemoteFileCommand._check(self,**args)

    def is_visible(self,**args):
        return AftpDeleteRemoteFileCommand._check(self,**args)

    def _check(self,**args):
        try:
            path = args['paths'][0]
        except Exception:
            path = self.view.file_name()

        paragrams = {}
        paragrams['path']   = path
        paragrams['command_type']   = 'file'
        paragrams['action'] = 'transfer'

        return valid(**paragrams)

# A command that delete folder from remote server
class AftpDeleteRemoteFolderCommand(sublime_plugin.TextCommand):
    def run(self,edit,**args):
        path = args['paths'][0]
        localDir = getLocalPath(path)
        if False == localDir:
            return False
        folder_name = getRemotePath(localDir,path)
        if False == folder_name:
            return False

        result = sublime.ok_cancel_dialog('Confirm delete remote folder: \n'+folder_name,'ok')
        if False == result:
            return False
        t = threading.Thread(target = executeCommand,args=('AftpDeleteRemoteFolder',path,))
        t.start()

    def is_enabled(self,**args):
        return AftpDeleteRemoteFolderCommand._check(self,**args)

    def is_visible(self,**args):
        return AftpDeleteRemoteFolderCommand._check(self,**args)

    def _check(self,**args):
        paragrams = {}
        paragrams['path']           = args['paths'][0]
        paragrams['command_type']   = 'folder'
        paragrams['action']         = 'transfer'

        return valid(**paragrams)

# A command that upload folder to remote server
class AftpUploadFolderCommand(sublime_plugin.TextCommand):
    def run(self,edit,**args):
        path = args['paths'][0]

        t = threading.Thread(target = executeCommand,args=('AftpUploadFolder',path,))
        t.start()

    def is_enabled(self,**args):
        return AftpUploadFolderCommand._check(self,**args)

    def is_visible(self,**args):
        return AftpUploadFolderCommand._check(self,**args)

    def _check(self,**args):
        paragrams = {}
        paragrams['path']   = args['paths'][0]
        paragrams['command_type']   = 'folder'
        paragrams['action'] = 'transfer'

        return valid(**paragrams)

# A command that download folder from remote server
class AftpDownloadFolderCommand(sublime_plugin.TextCommand):
    def run(self,edit,**args):
        path = args['paths'][0]

        t = threading.Thread(target = executeCommand,args=('AftpDownloadFolder',path,))
        t.start()

    def is_enabled(self,**args):
        return AftpDownloadFolderCommand._check(self,**args)

    def is_visible(self,**args):
        return AftpDownloadFolderCommand._check(self,**args)

    def _check(self,**args):
        paragrams = {}
        paragrams['path']   = args['paths'][0]
        paragrams['command_type']   = 'folder'
        paragrams['action'] = 'transfer'

        return valid(**paragrams)

# A command that compare file local with remote server
class AftpDiffRemoteFileCommand(sublime_plugin.TextCommand):
    def run(self,edit,**args):
        try:
            path = args['paths'][0]
        except Exception:
            path = self.view.file_name()

        t = threading.Thread(target = executeCommand,args=('AftpDiffRemoteFile',path,))
        t.start()

    def is_enabled(self,**args):
        return AftpDiffRemoteFileCommand._check(self,**args)

    def is_visible(self,**args):
        return AftpDiffRemoteFileCommand._check(self,**args)

    def _check(self,**args):
        try:
            path = args['paths'][0]
        except Exception:
            path = self.view.file_name()

        paragrams = {}
        paragrams['path']   = path
        paragrams['command_type']   = 'file'
        paragrams['action'] = 'transfer'

        return valid(**paragrams)

#Generate a config file for aftp connect
class AftpMapToRemoteCommand(sublime_plugin.TextCommand):

    def run(self,edit,**args):
        try:
            path = args['paths'][0]
        except Exception:
            path = self.view.file_name()

        if os.path.isfile(path):
            paths = os.path.split(path)
            path  = paths[0]

        conf_dir = os.path.join(path,'aftp-config.json')

        default_conf = open( DEFAULT_CONFIG_PATH,'rb' )
        conf = open(conf_dir,"wb")
        conf.write(default_conf.read())

        default_conf.close()
        conf.close()

    def is_enabled(self,**args):
        return AftpMapToRemoteCommand._check(self,**args)

    def is_visible(self,**args):
        return AftpMapToRemoteCommand._check(self,**args)

    def _check(self,**args):
        try:
            path = args['paths'][0]
        except Exception:
            path = self.view.file_name()

        paragrams = {}
        paragrams['path']   = path
        paragrams['command_type']   = 'none'
        paragrams['action'] = 'config'

        return valid(**paragrams)