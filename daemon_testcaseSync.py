#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Nov 14, 2018
daemon_testcaseSync.py: auto sync testcase daemon to ControlServer.
@author: Xiumiao Song
version: 1.0
'''

import sys, os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlserver import SQLClass
from common import model
import subprocess
from pyinotify import WatchManager, Notifier, ProcessEvent, IN_CREATE
from daemon_class import Daemon

# test case directory in DataServer
TCpath = "/opt/lenovo/AIS/testcase"
   

# Event handler to sync the testcase to all ControlServers
class testcaseEventHandler(ProcessEvent):
    def process_IN_CREATE(self, event): 
        # Create Linux database connection
        DS_engine = model.connectDB("Linux")
        # Create database session
        DS_Session = sessionmaker(bind=DS_engine)
        daemon_session = DS_Session()
        CS_query = daemon_session.query(SQLClass.controlserver).all()
	filename = os.path.join(event.path, event.name)
	print filename
	dstfile = filename[len(TCpath):]
	if os.path.isdir(filename):
            for Cserver in CS_query:
                 testcase_cmd='rsync -avzP --delete --password-file=/etc/rsyncd.scrt --timeout=60 %s/ root@%s::testcase-sync/%s' %(filename,Cserver.pubIPaddress,dstfile)
                 print Cserver.pubIPaddress
	         subprocess.call(testcase_cmd,shell=True)
	else:
            for Cserver in CS_query:
                 testcase_cmd='rsync -avzP --delete --password-file=/etc/rsyncd.scrt --timeout=60 %s root@%s::testcase-sync/%s' %(filename,Cserver.pubIPaddress,dstfile)
                 print Cserver.pubIPaddress
	         subprocess.call(testcase_cmd,shell=True)
	daemon_session.close()
	DS_engine.dispose()

class testcaseSync(Daemon):
    def __init__(self,
                 name,
                 pidfile='/tmp/testcaseSync.pid',
                 stdin='/dev/null',
                 stdout='dev/null',
                 stderr='/dev/null',
                 umask=022,
                 verbose=1):
        Daemon.__init__(self, pidfile, stdin, stdout, stderr, umask, verbose)
        # the name of thread
        self.name = name

    def run(self):
        sys.stdout.write('Daemon started with pid %d\n' % os.getpid())
        wm = WatchManager()
        mask = IN_CREATE
        notifier = Notifier(wm, testcaseEventHandler())
        wm.add_watch(TCpath, mask, rec=True)
        print 'Now starting monitor %s' % (TCpath)
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
    pname = 'testcaseSyncd'
    PIDFILE = '/tmp/testcaseSync.pid'
    LOG = '/var/log/testcaseSync.log'

    if len(sys.argv) != 2:
        print help_msg
        sys.exit(1)

    daemon = testcaseSync(
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
            print 'FileSync daemon [%s:%d] is running .....' % (
                daemon.name, daemon.getpid())
        else:
            print 'Daemon [%s] stopped.' % daemon.name
    else:
        print('Unkown command {!r}')
        print help_msg
        sys.exit(1)
   
