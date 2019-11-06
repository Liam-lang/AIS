#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Nov 14, 2018
daemon_isoimageSync.py: auto sync iso image daemon to ControlServer.
@author: Xiumiao Song
version: 1.4


Based on 1.0 add subprocess.call return code check and will rsyn until sucessfully

Based on 1.1 add the ISOmd5 calculation loop until ISOmd5=md5file or timeout(5min) to support cp and scp command to upload iso image

Based on 1.2 add the kernel version judgement for rc and no rc version

July 25,2019  Based on version 1.3, insert the VMware iso image info into DB
'''

import sys, os
import subprocess
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlserver import SQLClass
from pyinotify import WatchManager, Notifier, ProcessEvent, IN_CREATE
from daemon_class import Daemon
from common import model
from hashlib import md5
import time

# the directory that store iso image in DataServer
ISOpath = "/var/opt/lenovo/AIS/checkbase/ISO"

# check whether the event is valid or not
def valid_file(filename):
    global commonStr
    global isofile
    global f_md5
    global md5file
    if filename[:4] == "RHEL" or filename[:3] == "SLE":
        if filename[-7:] == ".tar.gz":
            pos=filename.find(".tar.gz")
        elif filename[-4:] == ".iso":
            pos=filename.find(".iso")
        else:
            print "Invalid event"
            return False
    elif filename[:6] == "kernel" and filename[-4:] == ".rpm": 
        pos=filename.find(".rpm")
    elif filename[:6] == "VMware" and filename[-4:] == ".iso":
        pos=filename.find(".iso")
    else:
        print "Invalid event."
        return False
    commonStr=filename[:pos]
    print "commonStr="+commonStr
    # check md5 file and iso file whether exist or not
    md5file="/var/opt/lenovo/AIS/checkbase/ISO/"+commonStr+".md5.txt"
    isofile="/var/opt/lenovo/AIS/checkbase/ISO/"+filename
    if os.path.exists(isofile) and os.path.exists(md5file):
        f = open(md5file,'r')
        line = f.readline().strip()
        pos1 = line.find(" ")
        f_md5 = line[:pos1].strip()
        md5f = line[pos1:].strip()
        if filename == md5f:
            return True
        else:
            print "iso name is different from the iso name in md5 file."
            return False
    else:
        print "There is no iso file or md5 file."
        return False

def new_version(new,old):
    posN1=model.findSubstring(new,".",1)
    posN2=model.findSubstring(new,".",2)
    posO1=model.findSubstring(old,".",1)
    posO2=model.findSubstring(old,".",2)
    if new[:posN1] > old[:posO1]:
        return True
    elif new[:posN1] == old[:posO1] and new[posN1+1:posN2] > old[posO1+1:posO2]:
        return True
    elif new[:posN1] == old[:posO1] and new[posN1+1:posN2] == old[posO1+1:posO2]:
        if "_" in new:
            posN3=model.findSubstring(new,"_",1)
            posN4=model.findSubstring(new,"-",1)
            new_rc=new[posN3+3:posN4]
        else:
            posN3=model.findSubstring(new,"-",1)
        if "_" in old:
            posO3=model.findSubstring(old,"_",1)
            posO4=model.findSubstring(old,"-",1)
            old_rc=old[posO3+3:posO4]
        else:
            posO3=model.findSubstring(old,"-",1)
        if new[posN2+1:posN3] > old[posO2+1:posO3]:
            return True
        elif new[posN2+1:posN3] == old[posO2+1:posO3]:
            if "_" not in new and "_" in old:
                return True
            elif "_" in new and "_" in old:
                if new_rc > old_rc:
                    return True
            else:
                print "the new version rc part is not bigger than old's"
                return False
        else:
            print "the new version three part is not bigger than old's"
            return False
    else:
        print "the new version one part or two part is smaller than old's"
        return False

# Event handler to sync the iso image to all ControlServers
class isoimageEventHandler(ProcessEvent):
    def process_IN_CREATE(self, event):
        # Create Linux database connection
        DS_engine = model.connectDB("Linux")
        # Create database session
        DS_Session = sessionmaker(bind=DS_engine)
        daemon_session = DS_Session()
        CS_query = daemon_session.query(SQLClass.controlserver).all()
        filename = os.path.join(event.path, event.name)
        print filename
        dstfile = filename[len(ISOpath):]
        if os.path.isfile(filename) and valid_file(event.name):
            # calculate the md5 of the file
            stime=time.time()
            while True:
                ISOmd5 = model.calMD5ForFile(isofile)
                print "ISOmd5="
                print ISOmd5
                if f_md5 == ISOmd5:
                    break
                if time.time()-stime > 600:
                    print "Calculate the iso image md5 value is timeout. Wrong iso image or md5file, please check!"
                    break
            print "Calculate iso file md5 use [%s] seconds"%(time.time()-stime)
            if ISOmd5 == f_md5:
                for Cserver in CS_query:
                    isoimage_cmd='rsync -avzP --delete --password-file=/etc/rsyncd.scrt --timeout=900 %s root@%s::isoimage-sync/%s' %(isofile,Cserver.pubIPaddress,dstfile)
                    md5file_cmd='rsync -avzP --delete --password-file=/etc/rsyncd.scrt --timeout=60 %s root@%s::isoimage-sync/%s' %(md5file,Cserver.pubIPaddress,md5file[len(ISOpath):])
                    print Cserver.pubIPaddress
                    flag=subprocess.call(isoimage_cmd,shell=True)
                    i = 0
                    while True:
                        i += 1
                        if flag == 0 or i > 3:
                            print "iso image rsync sucessfully"
                            break
                        else:
                            print "rsync failed, rsync iso image again!"
                            flag=subprocess.call(isoimage_cmd,shell=True)
                    subprocess.call(md5file_cmd,shell=True)
                    
                if event.name.find("kernel") == 0:
                    pos1=event.name.find("kernel-")
                    pos3=event.name.rfind(".rpm")
                    pos4=event.name[:pos3].rfind(".")
                    vs=event.name[pos1+7:pos4]
                    pf=event.name[pos4+1:pos3]
                    print "version=%s,platform=%s,md5=%s" %(vs,pf,ISOmd5)
                    LUK_query = daemon_session.query(SQLClass.os).filter(SQLClass.os.name == "Linux Upstream Kernel").first()
                    if LUK_query:
                        old_version=LUK_query.version
                        if new_version(vs,old_version):
                            try:
                                LUK_query.version=vs
                                LUK_query.imgname=event.name
                                LUK_query.driverflag='invalid'
                                LUK_query.md5=ISOmd5
                                daemon_session.flush()
                                daemon_session.commit()
                            except Exception as e:
                                daemon_session.rollback()
                                print e.message
                    else:
                        ositem=SQLClass.os(
                            name="Linux Upstream Kernel",
                            version=vs,
                            imgname=event.name,
                            phase="GA",
                            platform=pf,
                            driverflag="invalid",
                            md5=ISOmd5)
                        try:
                            daemon_session.add(ositem)
                            daemon_session.flush()
                            daemon_session.commit()
                        except Exception as e:
                            daemon_session.rollback()
                elif event.name.find("VMware") == 0:
                    str_vmware_list = event.name.split("-")
                    vs=str_vmware_list[3]
                    pf=str_vmware_list[4].split(".")[1]
                    print "version=%s,platform=%s,md5=%s" %(vs,pf,ISOmd5)
                    VMware_querys = daemon_session.query(SQLClass.os).filter(SQLClass.os.name == "VMware").all()
                    has_exist = False
                    for VMware_query in VMware_querys:
                        if vs == VMware_query.version:
                            has_exist = True
                    if has_exist == True:
                        print "New uploaded VMware iso image %s has existed in DB" %event.name
                    else:
                        ositem=SQLClass.os(
                            name="VMware",
                            version=vs,
                            imgname=event.name,
                            phase="GA",
                            platform=pf,
                            driverflag="invalid",
                            md5=ISOmd5)
                        try:
                            daemon_session.add(ositem)
                            daemon_session.flush()
                            daemon_session.commit()
                        except Exception as e:
                            daemon_session.rollback()
                            print e.message 
                            print e.message 
        daemon_session.close()
        DS_engine.dispose()

class isoimageSync(Daemon):
    def __init__(self,
                 name,
                 pidfile='/tmp/isoimageSync.pid',
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
        notifier = Notifier(wm, isoimageEventHandler())
        wm.add_watch(ISOpath, mask, rec=True)
        print 'Now starting monitor %s' % (ISOpath)
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
    pname = 'isoimageSyncd'
    PIDFILE = '/tmp/isoimageSync.pid'
    LOG = '/var/log/isoimageSync.log'

    if len(sys.argv) != 2:
        print help_msg
        sys.exit(1)

    daemon = isoimageSync(
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
