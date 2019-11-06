#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 18, 2018
daemontest.py: autotest daemon testing file.
@author: Neo
'''

import sys, os
from pyinotify import WatchManager, Notifier, ProcessEvent, IN_CREATE, IN_MODIFY

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")
from dbstore import initHandle, log
from daemon import Daemon


FSpath = "/home/information/status"


#Event handler
class EventHandler(ProcessEvent):  #文件变化的触发
    def process_IN_CREATE(self, event):
        text = "Create file: %s " % os.path.join(event.path, event.name)
        print text
        param = initHandle.initDB(event.path)
        log.logDB(param)

    def process_IN_MODIFY(self, event):
        text = "Modify file: %s " % os.path.join(event.path, event.name)
        print text


class AutoTest(Daemon):
    def __init__(self,
                 name,
                 pidfile='/tmp/autotest.pid',
                 stdin='/dev/null',
                 stdout='dev/null',
                 stderr='/dev/null',
                 umask=022,
                 verbose=1):
        Daemon.__init__(self, pidfile, stdin, stdout, stderr, umask, verbose)
        #the name of thread
        self.name = name

    def run(self):
        sys.stdout.write('Daemon started with pid %d\n' % os.getpid())
        wm = WatchManager()
        mask = IN_CREATE | IN_MODIFY
        notifier = Notifier(wm, EventHandler())
        wm.add_watch(FSpath, mask, rec=True)
        print 'now starting monitor %s' % (FSpath)
        while True:
            try:
                notifier.process_events()
                if notifier.check_events():
                    notifier.read_events()
            except KeyboardInterrupt:
                notifier.stop()
                break


if __name__ == '__main__':
    help_msg = 'Usage: python %s <start|stop|restart|status>' % sys.argv[0]
    pname = 'autotestd'
    PIDFILE = '/tmp/autotest.pid'
    LOG = '/tmp/autotest.log'

    if len(sys.argv) != 2:
        print help_msg
        sys.exit(1)

    daemon = AutoTest(
        pname, pidfile=PIDFILE, stdout=LOG, stderr=LOG, verbose=1)
    if sys.argv[1] == 'start':
        daemon.start()
    elif sys.argv[1] == 'stop':
        daemon.stop()
    elif sys.argv[1] == 'restart':
        daemon.restart()
    elif sys.argv[1] == 'status':
        alive = daemon.is_running()
        if alive:
            print 'AutoTest daemon [%s:%d] is running .....' % (
                daemon.name, daemon.getpid())
        else:
            print 'Daemon [%s] stopped.' % daemon.name
    else:
        print('Unkown command {!r}')
        print help_msg
        sys.exit(1)
