#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Dec 14, 2018
daemon_autoPackage.py: auto package the files under $MTSN which will be used for OS installation.
@author: Xiumiao Song
version: 1.0
'''

import sys, os
import subprocess
from pyinotify import WatchManager, Notifier, ProcessEvent, IN_CREATE
from daemon_class import Daemon
from hashlib import md5
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlserver import SQLClass
from common import model
import time

# the directory that storing the OSUnattendedFile in DataServer  
OSUFpath = "/etc/opt/lenovo/AIS/conf/OSUnattendedFile"

# calculate the md5 value of the file
def calMD5ForFile(file):
    statinfo = os.stat(file)
    if int(statinfo.st_size)/(1024*1024) >= 1000 :
        print "File size > 1000, move to big file..."
        return calMD5ForBigFile(file)
    m = md5()
    f = open(file, 'rb')
    m.update(f.read())
    f.close()
    return m.hexdigest()

def calMD5ForBigFile(file):
    m = md5()
    f = open(file, 'rb')
    buffer = 8192
    while 1:
        chunk = f.read(buffer)
        if not chunk :
            break
        m.update(chunk)
    f.close()
    return m.hexdigest()

# check the OSUatteded file is valid or not
def valid_file(filename):
    global commonStr    
    global isoname
    global isofile
    global f_md5
    if filename[:4] == "RHEL":
        pos=filename.find("-ks.cfg")
    elif filename[:3] == "SLE":
        pos=filename.find(".xml")
    else:
        print "Error:Invalid OS unattended file."
        return False
    commonStr=filename[:pos]
    print "commonStr="+commonStr
    # check md5 file and iso file whether exist or not
    isoname=commonStr+".iso"
    md5file="/var/opt/lenovo/AIS/checkbase/ISO/"+commonStr+".md5.txt"
    isofile="/var/opt/lenovo/AIS/checkbase/ISO/"+isoname
    if os.path.exists(isofile) and os.path.exists(md5file):
        f = open(md5file,'r')
        line = f.readline().strip()
        pos = line.find(" ")
        f_md5 = line[:pos].strip()
        md5f = line[pos:].strip()
        if isoname == md5f:
            return True
        else:
            print "iso name is different from the iso name in md5 file."
            return False
    else:
        print "There is no iso file or md5 file which are corresponding to the OSUnattended file."
        return False

# Event handler
class OSUnattendedFileEventHandler(ProcessEvent):
    def process_IN_CREATE(self, event):
	filename = os.path.join(event.path, event.name)
	print filename
	if os.path.isfile(filename) and valid_file(event.name):
            stime=time.time()
            # compare the OS iso file md5 and the md5 value stored in the md5 file
            while True:
                ISOmd5=calMD5ForFile(isofile)
                if f_md5 == ISOmd5:
                    break
                if time.time()-stime > 20:
                    print "Use too long time to calculate the md5 value. Wrong iso image or md5file, please check"
                    break
            print "Calculate iso file md5 use [%s] seconds"%(time.time()-stime)
            if ISOmd5 == f_md5:
                # execute the auto package function
                pack_cmd='./opt/lenovo/AIS/www/DataServer/autoPackage.sh %s' %(commonStr) 
	        subprocess.call(pack_cmd,shell=True)
                # if ISOmd5 and isoname don't exist in OS DB, then insert the iso info to os table
                engine = model.connectDB("Linux")
                print "Create database session..."
                DBSession = sessionmaker(bind=engine)
                osSession = DBSession()
                try:
                    OS_query = osSession.query(SQLClass.os).filter(or_(SQLClass.os.md5 == ISOmd5,SQLClass.os.imgname == isoname)).all() 
                except Exception as e:
                    osSession.rollback()
                    print e.message
                if len(OS_query) == 0:
                    if commonStr.find("RHEL") == 0:
                        nm = "Red Hat Enterprise Linux Server"
                        pos1 = model.findSubstring(commonStr,"-",1)
                        pos2 = model.findSubstring(commonStr,"-",2)
                        pos3 = model.findSubstring(commonStr,"-",3)
                        pos4 = model.findSubstring(commonStr,"-",4)
                        pos_dvd1=commonStr.find("-dvd1")
                        if pos4 == pos_dvd1:
                            pf=commonStr[pos3+1:pos_dvd1]
                        else:
                            pf=commonStr[pos4+1:pos_dvd1]
                        osv=commonStr[pos1+1:pos2]
                        ph=commonStr[pos2+1:pos3]
                    elif commonStr.find("SLE") == 0:
                        nm="SUSE Enterprise Linux Server"
                        pos1 = model.findSubstring(commonStr,"-",1)
                        pos2 = model.findSubstring(commonStr,"-",2)
                        pos3 = model.findSubstring(commonStr,"-",3)
                        pos4 = commonStr.find("-DVD-")
                        pos5 = commonStr.find("-DVD1") 
                        phApf = commonStr[pos4+5:pos5]
                        pos6 = phApf.find("-")
                        if "SP" in commonStr[pos2+1:pos3]:
                            osv = commonStr[pos1+1:pos2]+"."+commonStr[pos2+3:pos3]
                        else:
                            osv = commonStr[pos1+1:pos2]
                        ph=phApf[pos6+1:]
                        pf=phApf[:pos6]
                    print "name=%s,version=%s,imgname=%s,phase=%s,platform=%s,md5=%s" %(nm,osv,isoname,ph,pf,ISOmd5)
                    ositem = SQLClass.os(
                        name=nm,
                        version=osv,
                        imgname=isoname,
                        phase=ph,
                        platform=pf,
                        driverflag="invalid",
                        md5=ISOmd5)
                    try:
                        osSession.add(ositem)
                        osSession.flush()
                        osSession.commit()
                    except Exception as e:
                        osSession.rollback()
                        print e.message
                osSession.close()
                engine.dispose()
                
                


class AutoPackage(Daemon):
    def __init__(self,
                 name,
                 pidfile='/tmp/AutoPackage.pid',
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
        notifier = Notifier(wm, OSUnattendedFileEventHandler())
        wm.add_watch(OSUFpath, mask, rec=True)
        print 'Now starting monitor %s' % (OSUFpath)
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
    pname = 'autoPackaged'
    PIDFILE = '/tmp/AutoPackage.pid'
    LOG = '/var/log/AutoPackage.log'

    if len(sys.argv) != 2:
        print help_msg
        sys.exit(1)

    daemon = AutoPackage(
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
            print 'autoPackage daemon [%s:%d] is running .....' % (
                daemon.name, daemon.getpid())
        else:
            print 'Daemon [%s] stopped.' % daemon.name
    else:
        print('Unkown command {!r}')
        print help_msg
        sys.exit(1)
