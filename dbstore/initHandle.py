#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 13, 2018
initHandle.py: check the file under status and get the system, os information 
check the file under status folder. The filename is related to creation time,
OS version, system model.
Change the file name to done_time_system_osnameosversion when completing
operation.
@author: Neo
Version: 1.0
'''
import sys, os, re
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")
from sqlserver import SQLClass
from common import rdgenerator, autotestlog, model

# global variables
osname = ""
osversion = ""
logparam = {'sysosid': '', 'logdir': ''}
param = {'model': '', 'imgname': '', 'processor': '', 'BIOS': '', 'Mode': model.modEnum.UEFI.value, 'Engineer': '', 'Tester': ''}
osdict = {
    'RedHat': 'Red Hat Enterprise Linux Server',
    'SUSE': 'SUSE Enterprise Linux Server',
    'kernel': 'Linux Upstream Kernel'
}


# 递归遍历指定目录，显示目录下的所有文件名
def allFiles(rootdir):
    global osname, osversion, param
    extso = '_'
    list_dirs = os.walk(rootdir)
    for root, dirs, files in list_dirs:
        ## get the system and osname
        for f in files:
            if f.find('.txt') >= 0 and f.find('driver') == -1:
                filename = os.path.join(root, f)
                sPos = model.findSubstring(f, extso, 3)
                ePos = model.findSubstring(f, extso, 4)
                abr_osname = f[sPos + 1:ePos]
                osname = osdict[abr_osname]
                sPos = f.find('.txt')
                osversion = f[ePos + 1:sPos]
                sPos = model.findSubstring(f, extso, 2)
                ePos = model.findSubstring(f, extso, 3)
                param['model'] = f[sPos + 1:ePos]
                ePos = model.findSubstring(f, extso, 1)
                sPos = f.find('.txt')
                logparam['logdir'] = abr_osname + "/" + osversion + "/" + f[ePos -3:sPos]
                if os.path.getsize(filename) == 0:
                    # why need to rename
                    rd = rdgenerator.id_generator()
                    newname = f[0:-3] + rd
                    os.rename(filename, os.path.join(root, newname))
                    print "Empty file content"
                    return -1
                ret = imgnameHandle(filename)
                rd = rdgenerator.id_generator()
                newname = f[0:-3] + rd
                os.rename(filename, os.path.join(root, newname))
                if ret == 0:
                        return 0
                else:
                        return -1
            else:
                pass


# Obtain the system configuration information
def imgnameHandle(filename):
    global param
    try:
        fopen = open(filename, 'r')
        lines = fopen.readlines()
        for line in lines:
            line = line.strip('\n')
            if line.find('Version') >= 0:
                param['processor'] = line[8:]
            elif line.find("ISO") > 0:
                param['imgname'] = line
            elif line.find('BIOS') >= 0:
                param['BIOS'] = line[5:]
            elif line.find('Mode') >= 0:
                param['Mode'] = line[5:]
            elif line.find('Engineer') >= 0:
                param['Engineer'] = line[9:]
            elif line.find('Tester') >=0:
                param['Tester'] = line[7:]
            fopen.close()
            return 0
    except IOError:
        print "Open file failed"
        return -1


# update the system, os information in the database
def updatedb(session):
    global osname, osversion, param
    var_osid = ''
    var_sysid = ''
    thinkserver_arr = ['rd', 'td', 'rs', 'ts', 'rq']
    thinksystem_arr = ['sr', 'st']
    if param['model'][0:2] in thinkserver_arr:
        serie = 'thinkserver'
    elif re.match('x', param['model']):
        serie = 'systemX'
    elif param['model'][0:2] in thinksystem_arr:
        serie = 'thinksystem'
    else:
        print "No matched system series found!"
    # check if os already added in the database
    flag = session.query(
        SQLClass.os).filter(SQLClass.os.imgname == param['imgname']).first()
    if flag:
        print "osid is:", flag.osid
        var_osid = flag.osid
    else:
        ositem = SQLClass.os(
            name=osname,
            platform=model.plmEnum.x86_64.value,
            version=osversion,
            imgname=param['imgname'])
        try:
            session.add(ositem)
            session.flush()
            print "osid is:", ositem.osid
            var_osid = ositem.osid
            session.commit()
        except Exception as e:
            session.rollback()
            if e.message.find("Duplicate entry") < 0:
                autotestlog.logger.error(e.message)
    # check if system already added in the database
    flag = session.query(SQLClass.system).filter(
        and_(SQLClass.system.model == param['model'],
            SQLClass.system.processor == param['processor'],
            SQLClass.system.biosmode == param['Mode'],
            SQLClass.system.biosver == param['BIOS'])).first()
    if flag:
        print "system id is:", flag.systemid
        var_sysid = flag.systemid
    else:
        codename_tb = session.query(SQLClass.codename).filter(SQLClass.codename.model==param['model'].upper()).first()
        var_codename = ""
        if codename_tb:
            var_codename = codename_tb.codename
        sysitem = SQLClass.system(
            series=serie, model=param['model'], processor=param['processor'],
            biosmode=param['Mode'], biosver=param['BIOS'], codename=var_codename)
        try:
            session.add(sysitem)
            session.flush()
            print "system id is:", sysitem.systemid
            var_sysid = sysitem.systemid
            session.commit()
        except Exception as e:
            session.rollback()
            if e.message.find("Duplicate entry") < 0:
                autotestlog.logger.error(e.message)
    if var_osid and var_sysid:
        logfile = model.featureLogDir + logparam['logdir']
        flag = session.query(SQLClass.system_os).filter(
            SQLClass.system_os.logfile == logfile).first()
        if flag:
            print "system_os id is:", flag.system_osid
            logparam['sysosid'] = flag.system_osid
        else:
            sysositem = SQLClass.system_os(
                systemid=var_sysid, osid=var_osid, logfile=logfile,
                tester=param['Tester'], engineer=param['Engineer'])
            try:
                session.add(sysositem)
                session.flush()
                print "system_os id is:", sysositem.system_osid
                logparam['sysosid'] = sysositem.system_osid
                session.commit()
            except Exception as e:
                session.rollback()
                if e.message.find("Duplicate entry") < 0:
                    autotestlog.logger.error(e.message)
        return 0
    else:
        text = "System or OS not found in the database."
        autotestlog.logger.error(text)
        return -1


# initDB(): Handle status file and update system/os tables
def initDB(rootdir):
    engine = model.connectDB("Linux")
    print "Create database session..."
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    print "Done."
    print "Create metadata object..."
    meta = MetaData(bind=engine)
    meta.reflect(bind=engine)
    model.Base.metadata.create_all(engine, checkfirst=True)
    print "Done."
    print "Searching file change...."
    ret = allFiles(rootdir)
    if ret == 0:
        print "Updating system and os table"
        ret = updatedb(session)
        if ret == 0:
            return logparam
            print "Done."
    else:
        text = "Handle status file error."
        autotestlog.logger.error(text)
    session.close()
    engine.dispose()
    return -1


if __name__ == '__main__':
    rootdir = model.statusDir
    initDB(rootdir)
