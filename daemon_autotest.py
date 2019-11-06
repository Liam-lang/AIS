#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 18, 2018
daemon_autotest.py: autotest daemon testing file.
@author: Neo
version: 1.0
'''

import sys, os
from pyinotify import WatchManager, Notifier, ProcessEvent, IN_CREATE
from daemon_class import Daemon

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")
from dbstore import initHandle, log, driver
from analyze import pciresult, logresult, report
from common import model


# Event handler
class EventHandler(ProcessEvent):
    def process_IN_CREATE(self, event):
        sys.stdout.write("EventHandler() start.\n")
        sys.stdout.write("Event.path is " + event.path + "\n")
        sys.stdout.write("Event.name is " + event.name + "\n")
        log_ret = -1
        pci_ret = -1
        flag_type = -1

        root = event.path
        statusFileName = event.name
        if statusFileName.startswith('.'):
            statusFileName = statusFileName[:statusFileName.rfind(".")].strip(".")
        sys.stdout.write("Create file: %s \n" % (statusFileName))
        statusFilePath = os.path.join(root, statusFileName)
        sys.stdout.write("Full file path: %s \n" % (statusFilePath))

        # Information handle begin.
        if statusFileName.startswith('log') and statusFileName.endswith('txt'):
            logparam = initHandle.initDB(event.path)
            if logparam != -1:
                logretparam = log.logDB(logparam)
                if logretparam != -1:
                    log_ret = logresult.logAnalyze(logretparam)
                else:
                    sys.stderr.write(
                    "Update log information to database fail.")
            # print "Update log information to database fail."
            else:
                sys.stderr.write(
                "Update system/OS information to database fail.\n")
        # print "Update system/OS information to database fail."
        # Driver information handle
        elif statusFileName.startswith('driver') and statusFileName.endswith('txt'):
            #get driver dir from root
            driverdir = root[len(model.statusDir)+1:]
            sys.stdout.write("Driverdir is " + driverdir + "\n")

            #get imgName and taskId from fileName
            #statusName = driver_ + driverName
            imgName,taskID = model.getImgTask(statusFileName.lstrip("driver_"))
            sys.stdout.write("Get info from status file. imgName is %s , task ID is %s.\n"%(imgName,taskID))

            ret=driver.driverDB(driverdir, imgName, taskID)
            if ret == model.RET_FAILED:
                sys.stdout.write("Write driver file info to driver_table failed.\n")
            if imgName.lower().startswith("kernel"):
                sys.stdout.write("kernel is no need to go to pciAnalyze.\n")
            pci_ret = pciresult.pciAnalyze(taskID)

            #rename status file after analyze because sync process product hidden file like .xxxx.randam
            #can't rename status file before hidden file rename to real file
            try:
                newfilename = statusFilePath.rstrip(".txt")
                os.rename(statusFilePath, newfilename)
                sys.stdout.write("rename status file name is successed.\n")
            except Exception as e:
                sys.stderr.write("rename status file name is failed.\n")
                print repr(e)
                pass

        # Add report analyze function
        else:
            flag_type = 1

        if flag_type == 1:
            sys.stderr.write("Strange file format created.\n")
            try:
                os.remove(statusFilePath)
            except Exception as e:
                sys.stderr.write(e.message)
                pass
        elif log_ret != -1:
            report_ret = report.testReport(logparam['sysosid'])
            if report_ret == -1:
                sys.stderr.write("Create the test report fail.\n")
        elif pci_ret != -1:
            print "Create driver report success.\n"
        else:
            sys.stderr.write("Create log analysis report or driver analysis report failed.\n")


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
        # the name of thread
        self.name = name

    def run(self):
        sys.stdout.write('Daemon started with pid %d\n' % os.getpid())
        wm = WatchManager()
        mask = IN_CREATE
        notifier = Notifier(wm, EventHandler())
        wm.add_watch(model.statusDir, mask, rec=True, auto_add=True)
        print 'Now starting monitor %s' % (model.statusDir)
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
    PIDFILE = model.tmpDir + 'autotest.pid'
    LOG = model.logDir + 'autotest.log'

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
