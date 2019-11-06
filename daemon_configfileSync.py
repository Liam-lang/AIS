#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Nov 14, 2018
daemon_configfileSync.py: auto sync config file to each ControlServer daemon.
@author: Xiumiao Song
version: 1.1

July 24,2019 Based on version 1.0 sync linux config file before adding PCI ID info into DB,
             but sync VMware inbox config file after writing the PCI ID info to DB done.
             Put the PCIID file process to the PCIID_file_process function
'''

import sys, os
import subprocess
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlserver import SQLClass
from common import model
from pyinotify import WatchManager, Notifier, ProcessEvent, IN_CREATE
from daemon_class import Daemon
import pandas as pd
import math
import numpy as np

# the directory that storing the configfile in DataServer  
CFpath = "/etc/opt/lenovo/AIS/conf/task/"


# PCIID_file_process function will process the pciid file download from IO website
# paremeter: filedir is the pciid file directory 
def PCIID_file_process(filedir):
    # Create Linux database connection
    DS_engine = model.connectDB("Linux")
    # Create database session
    DS_Session = sessionmaker(bind=DS_engine)
    daemon_session = DS_Session()

    # delete all the data in pciid table
    try:
    	daemon_session.query(SQLClass.pciid).delete(synchronize_session=False)
    	daemon_session.commit()
    except Exception as e:
    	daemon_session.rollback()
    	print e.message
    # insert the pciid info to the pciid table
    files = os.listdir(filedir)
    ## get the pciid excel file downloaded from IO website
    if files:
    	for f in files:
            if f.find('.xlsx') >= 0:
            	filename = os.path.join(filedir, f)
  		pf=pd.read_excel(io=filename)
            	print "len(pf)=%d" %(len(pf))
                for i in range(0,len(pf)):
                    vd=pf.ix[i,"vendor"]
                    desc=pf.ix[i,"String name"]
                    VD_ID=pf.ix[i,"Device PCI ID(VendorID:DeviceID)"]
                    posvd=VD_ID.find(":")
                    vid=VD_ID[:posvd]
                    did=VD_ID[posvd+1:]
                    SUBVD_ID=pf.ix[i,"SubvendorID:SubdeviceID(SubdeviceID may not unique)"]
                    print "SUBVD_ID="
                    print SUBVD_ID
                    print "the type of SUBVD is "
                    print type(SUBVD_ID)
                    if isinstance(SUBVD_ID,float) and np.isnan(SUBVD_ID):
                        subvid=""
                        subdid=""
                    else:
                        possubvd=SUBVD_ID.find(":")
                        subvid=SUBVD_ID[:possubvd]
                        subdid=SUBVD_ID[possubvd+1:]
                    pro=pf.ix[i,"Project(Initial Introduced)"]             
                    pciidItem=SQLClass.pciid(
                        vendor=vd,
                        description=desc,
                        vendorid=vid,
                        deviceid=did,
                        subvendorid=subvid,
                        subdeviceid=subdid,
                        project=pro,   
                        status="valid")
                    try:
                        daemon_session.add(pciidItem)
                        daemon_session.flush()
                        daemon_session.commit()
                    except Exception as e:
                        daemon_session.rollback()
                        print e.message

            os.remove(filename)
            print "delete pciid file %s" %(f)
    else:
        print "There is no excel file in the %s directory" %(filedir)
    daemon_session.close()
    DS_engine.dispose()


# Event handler
class ConfigfileEventHandler(ProcessEvent):
    def process_IN_CREATE(self, event):
        # Create Linux database connection
        DS_engine = model.connectDB("Linux")
        # Create database session
        DS_Session = sessionmaker(bind=DS_engine)
        daemon_session = DS_Session()
        filename = os.path.join(event.path, event.name)
        print filename
        dstfile = filename[len(CFpath):]
        if os.path.isfile(filename):        
            pos1 = model.findSubstring(event.name,"_",1)
            pos2 = model.findSubstring(event.name,'_',2)
            CS_IP= event.name[pos1+1:pos2]
            VMware_flag = False
            print "CS_IP="+CS_IP
            CS_query = daemon_session.query(SQLClass.controlserver).filter(SQLClass.controlserver.pubIPaddress == CS_IP).all()
            if  len(CS_query) == 1:
                with open(filename,"r") as file_obj:
                    file_lines = file_obj.readlines()
                for line in file_lines:
                    if model.findSubstring(line,"VMware",1) >= 0:
                        vmware_osname = line
                        vmware_version = line.split("-")[3][:5]
                        VMware_flag = True
                if VMware_flag == False:
                    sync_cmd='rsync -avzP --delete --password-file=/etc/rsyncd.scrt --timeout=60 %s root@%s::configfile-sync/%s' %(filename,CS_IP,event.name)
                    print sync_cmd
                    subprocess.call(sync_cmd,shell=True)
                taskT = event.name[:pos1]
                if taskT == "Inbox":
                   PCIID_file_process("/var/opt/lenovo/AIS/checkbase/PCIID/")
                   if VMware_flag == True:
                        vmware_common_name = vmware_osname.strip()
                        print "vmware_common_name="
                        print vmware_common_name
                        taskID = event.name.split("_")[2][:-4]
                        txtfile_name = '%s.txt'%(vmware_common_name)
                        txtfile_newname = '%s_%s.txt'%(vmware_common_name,taskID)
                        txtfile_path = '/var/opt/lenovo/AIS/collect/drivers/VMware/%s/%s'%(vmware_version,txtfile_name)
                        newfile_path = '/var/opt/lenovo/AIS/collect/drivers/VMware/%s/%s'%(vmware_version,txtfile_newname)
                        print txtfile_path
                        print newfile_path
                        chname_cmd='mv %s %s' %(txtfile_path,newfile_path)
                        print chname_cmd
                        subprocess.call(chname_cmd,shell=True)
                        sync_cmd='rsync -avzP --delete --password-file=/etc/rsyncd.scrt --timeout=60 %s root@%s::configfile-sync/%s' %(filename,CS_IP,event.name)
                        print sync_cmd
                        subprocess.call(sync_cmd,shell=True)
            else:
                print "The CS_IP in the task file doesn't exist in controlserver table" 
        daemon_session.close()
        DS_engine.dispose()

class ConfigfileSync(Daemon):
    def __init__(self,
                 name,
                 pidfile='/tmp/configfileSync.pid',
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
        notifier = Notifier(wm, ConfigfileEventHandler())
        wm.add_watch(CFpath, mask, rec=True)
        print 'Now starting monitor %s' % (CFpath)
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
    pname = 'configfileSyncd'
    PIDFILE = '/tmp/ConfigfileSync.pid'
    LOG = '/var/log/ConfigfileSync.log'

    if len(sys.argv) != 2:
        print help_msg
        sys.exit(1)

    daemon = ConfigfileSync(
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
            print 'ConfigFileSync daemon [%s:%d] is running .....' % (
                daemon.name, daemon.getpid())
        else:
            print 'Daemon [%s] stopped.' % daemon.name
    else:
        print('Unkown command {!r}')
        print help_msg
        sys.exit(1)
