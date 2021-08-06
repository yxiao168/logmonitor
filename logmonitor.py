#!/usr/bin/env python
#
#
# logmonitor.py
#
# Yanming Xiao
# yanming_xiao@yahoo.com
#
# Run mode:
#   logmonitor.py {logmonitor.ini}
#
# Debug mode:
#   python -m pudb.run logmonitor.py {logmonitor.ini}
#
#
import sys
import os
import signal
import re
import ConfigParser
import time
import datetime
import platform
import shutil
import commands
#
import pprint


class Monitor:
    def __init__(self, section):
        self._PatternList = {}
        self._ResultList = {}
        self._section = section
        self._file = ''
        self._st_size = 0
        self._st_mtime = 0

    def Output(self):
        print '--- monitor ---'
        pprint.pprint(self._section)
        pprint.pprint(self._file)
        pprint.pprint(self._st_size)
        pprint.pprint(self._st_mtime)
        pprint.pprint(self._PatternList)


def DebugOutput():
    if _logmonitor_['debug'] == '1':
        print('--- globals ---')
        pprint.pprint(_logmonitor_)
        print '--- _monitorlist_ ---'
        for monitor in _monitorlist_:
            monitor.Output()
        print '--- _currentStats_ ---'
        pprint.pprint(_currentStats_)


def BackupLogFiles(destDir):
    WriteLine('Backup Subdir: ' + destDir)
    _f_.flush()
    try:
        os.makedirs(destDir)
    except:
        pass
    for monitor in _monitorlist_:
        try:
            shutil.copy(monitor._file, destDir)
        except:
            pass
    # copy the application log too
    shutil.copy(_reportfile_, destDir)
    #  run an external command when matching happens.
    if _logmonitor_.has_key('commandWhenMatching'):
        cmd = ReplaceVariables(_logmonitor_['commandWhenMatching'], _logmonitor_)
        ExecShellCommand(cmd)


def CheckPatterns(monitor, strLine):
    modTime = time.localtime(_currentStats_[monitor._file][1])
    modTime2hr = time.strftime("%m/%d/%Y %H:%M:%S", modTime)
    fMatch = False
    for pattern in monitor._PatternList:
        fShowLineOnce = True
        allPatterns = (monitor._PatternList[pattern]).split(',')
        lenPostNegative = len(allPatterns)
        p = re.compile(allPatterns[0])
        fMatchOnePattern = p.match(strLine)
        # eliminate false-positive maching
        if fMatchOnePattern:
            for i in range(1, lenPostNegative):
                n = re.compile(allPatterns[i])
                if n.match(strLine):
                    fMatchOnePattern = False
        # matching
        if fMatchOnePattern:
            if fShowLineOnce:
                WriteLine('--- ' + modTime2hr + '   ' + monitor._file + ' ---')
                WriteLine('Line   : ' + strLine)
                fShowLineOnce = False
            if _logmonitor_['showPatterns'] == '1':
                WriteLine('Pattern: ' + pattern + '=' + monitor._PatternList[pattern])
            monitor._ResultList[pattern] += 1
        # if any pattern matches
        fMatch = fMatch or fMatchOnePattern
    return (fMatch)


def TailFile(monitor):
    fh = open(monitor._file, 'rb')
    fh.seek(monitor._st_size)
    line = ' '
    fMatch = False
    while line:
        line = fh.readline()
        if line:
            fMatch = CheckPatterns(monitor, line[:-1]) or fMatch
    fh.close()
    return (fMatch)


def fileStat(filename):
    try:
        st_results = os.stat(filename)
    except:
        return (0, 0)
    return (st_results[6], st_results[8])


def GetCurrentTime():
    ts = datetime.datetime.now().__str__()
    ts = ts.replace("-","")
    ts = ts.replace(":","")
    ts = ts.replace(" ","_")
    ts = ts.replace(".","_")
    return (ts)


def StartMonitoring():
    global _logmonitor_
    global _currentStats_
    DebugOutput()
    subDir = 'errlogs'
    while True:
        fMatch = False
        for monitor in _monitorlist_:
            _currentStats_[monitor._file] = fileStat(monitor._file)
            if (_currentStats_[monitor._file][0] != monitor._st_size) or \
                (_currentStats_[monitor._file][1] != monitor._st_mtime):
                fMatch = TailFile(monitor) or fMatch
                monitor._st_size = _currentStats_[monitor._file][0]
                monitor._st_mtime = _currentStats_[monitor._file][1]
                if fMatch:
                    subDir = GetCurrentTime()
                    _logmonitor_['subDir'] = subDir
        # back up all files
        if fMatch:
            BackupLogFiles(subDir)

        DebugOutput()
        time.sleep(_interval_)

#
# http://stackoverflow.com/questions/4914277/how-to-empty-a-file-using-python
# open(filename, 'w').close()
#
def InitLogs():
    for monitor in _monitorlist_:
        open(monitor._file, 'w').close()
    WriteLine(' Clearing all logs before monitoring')


def CreateRptFile(logMonitorCfgFile):
    global _f_
    global _reportfile_
    if _logmonitor_.has_key('reportpath'):
        reportpath = _logmonitor_['reportpath']
    else:
        reportpath = '.'
    _reportfile_ = reportpath + '/' + logMonitorCfgFile.replace('.ini', '')
    if _logmonitor_['overwriteoldreport'] == '1':
        _reportfile_ += '.rpt'
    else:
        _reportfile_ += '_' + GetCurrentTime() + '.rpt'

    _f_ = open(_reportfile_, "w+")
    Version()
    WriteLine("")


def ReadConfigSection(config, section, sectionDictionary):
    try:
        options = config.options(section)
    except ConfigParser.NoSectionError:
        WriteLine("\n\nError:")
        WriteLine('Section [' + section +  '] not exists.')
        os._exit(1)
    for option in options:
        sectionDictionary[option] = config.get(section, option)


def ReadMonitorSection(config, section, monitor):
    try:
        options = config.options(section)
    except ConfigParser.NoSectionError:
        WriteLine("\n\nError:")
        WriteLine('Section [' + section +  '] not exists.')
        os._exit(1)
    for option in options:
        if option == 'file':
            monitor._file = config.get(section, option)
        else:
            monitor._PatternList[option] = config.get(section, option)
            monitor._ResultList[option] = 0


def ReadConfigFile(config, sectionDictionary):
    global _logmonitor_
    global _monitorlist_
    global _interval_
    ReadConfigSection(config, 'logmonitor', sectionDictionary)
    _interval_ = int(_logmonitor_['interval'])
    for logFileSection in _logmonitor_['logs'].split(','):
        monitor = Monitor(logFileSection)
        ReadMonitorSection(config, logFileSection, monitor)
        _monitorlist_.append(monitor)


def ReadLogMonitorCfgFile(logMonitorCfgFile, sectionDictionary):
    config = ConfigParser.ConfigParser()
    config.optionxform = str
    config.read(logMonitorCfgFile)
    ReadConfigFile(config, sectionDictionary)


def ExecCfgFile(logMonitorCfgFile):
    global _logmonitor_
    WriteLine('Running Configuration File: ' + logMonitorCfgFile)
    # read .ini into _logmonitor_
    _logmonitor_['logMonitorCfgFile'] = logMonitorCfgFile
    ReadLogMonitorCfgFile(logMonitorCfgFile, _logmonitor_)
    # create result file
    CreateRptFile(logMonitorCfgFile)
    WriteLine("\n Subject: " + _logmonitor_['subject'])
    #  Clearing all logs before monitoring
    if _logmonitor_['initLogs'] == '1':
        InitLogs()
    # run external command
    if _logmonitor_.has_key('command'):
        cmd = ReplaceVariables(_logmonitor_['command'], _logmonitor_)
        ExecShellCommand(cmd)
    WriteLine("\n Checking log files every " + str(_interval_) + " seconds ...\n\n\n")


def ReplaceVariables(line, varDict):
    pattern = '\${(?P<variable>\w+)}'
    regex = re.compile(pattern)
    variables = regex.findall(line)
    for v in variables:
        if varDict.has_key(v):
            oldstring = '${' + v + '}'
            newstring = varDict[v]
            line = line.replace(oldstring, newstring)
        else:
            WriteLine('Variable ${' + v + '} is not defined.')
            os._exit(1)
    return (line)

def ExecShellCommand(cmd):
    WriteLine(" Running command: " + cmd)
    output = (0, ' ')
    output = commands.getstatusoutput(cmd)
    WriteLine(output[1])
    if output[0] != 0:
        WriteLine("Error: execution of " + cmd + " is failed.")
        os._exit(1)

def WriteLine(line):
    try:
        print line
        if _f_ != None:
            _f_.write(line + "\n")
    except IOError:
        pass


def Summary():
    WriteLine("\n=== Summary of Matching Counts ===")
    for monitor in _monitorlist_:
        WriteLine('--- ' + monitor._file + ' ---')
        for pattern in monitor._PatternList:
            WriteLine(pattern + ' : ' + str(monitor._ResultList[pattern]))
    WriteLine("\n")


def signal_handler(signal, frame):
    Summary()
    print 'You pressed Ctrl+C!'
    WriteLine("\n")
    _f_.close()
    sys.exit(0)


def Version():
    WriteLine("\n logmonitor " + version + " - Log Monitor\n")


def Usage():
    Version()
    WriteLine("Usage:\n$ python logmonitor.py {logmonitor.ini}\n")


def main():
    if len(sys.argv) == 2:
        if os.path.exists(sys.argv[1]):
            signal.signal(signal.SIGINT, signal_handler)
            print 'Press Ctrl+C to exit'
            ExecCfgFile(sys.argv[1])
            StartMonitoring()
        else:
            WriteLine('INI file ' + sys.argv[1] + ' not exists.')
            os._exit(1)
    else:
        Usage()


#
# starts here.
#
version="1.10"
_f_ = None
_reportfile_ = ''
_interval_ = 1
#
_logmonitor_ = {}
_monitorlist_ = []
_currentStats_ = {}
#
if __name__ == '__main__':
    main()
