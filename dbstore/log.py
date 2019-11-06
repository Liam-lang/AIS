#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 09, 2018
log.py: handle the log information under
model.featureLogDir/OSVs/version/log_time_machine_OS/
dmesg and messages file is under logcheck directory
@author: Neo
Version: 1.0
'''
import sys, os, md5
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")
from sqlserver import SQLClass
from common import autotestlog, model

# global variables
src = ""
logfile = ""
var_sysosid = ""
sev = (model.typEnum.fail, model.typEnum.warning, model.typEnum.error)

# log dictionary
log = {
    'information': '',
    'type': '',
    'source': '',
    'status': '',
    'logfile': ''
}


# 递归遍历指定目录，显示目录下的所有文件名
def allFiles(rootdir, session):
    global src, logfile
    dmesg = 'dmesg'
    messages = 'messages'
    extso = '_'
    list_dirs = os.walk(rootdir)
    for root, dirs, files in list_dirs:
        # get the system and osname
        for f in files:
            if f == dmesg or f == messages:
                src = f
                filename = os.path.join(root, f)
                sPos = model.findSubstring(filename, extso, 3)
                ePos = model.findSubstring(filename, extso, 4)
                osname = filename[sPos + 1:ePos]
                Pos = filename.find('/logcheck')
                if Pos >= 0:
                    logfile = filename[:Pos]
                    log['logfile'] = logfile
                    if f == dmesg:
                        dmesgHandle(filename, session)
                    if f == messages and osname == 'SUSE':
                        susemsgHandle(filename, session)
                    if f == messages and osname == 'RedHat':
                        rhelmsgHandle(filename, session)
                    return 0
                else:
                    print "Can't find the logcheck directory"
                    return -1


# update log_system_os table
def checksysos(param, session):
    global logfile, var_sysosid
    # check if system_os exists in the system_os table
    flag = session.query(SQLClass.system_os).filter(
        SQLClass.system_os.system_osid == param).first()
    if flag:
        print "system_os id is:", flag.system_osid
        var_sysosid = flag.system_osid
        return var_sysosid
    else:
        print "No respective system and os item in the system_os table, or logfile is an empty string."
        return -1 


# handle log file - dmesg
def dmesgHandle(filename, session):
    global src, var_sysosid, sev
    flag = False
    var_logid = ''
    fopen = open(filename, 'r')
    data = fopen.read()
    lines = data.split('\n')
    log['source'] = src
    for eachLine in lines:
        eachLine = eachLine[eachLine.find(']') + 1:]
        if eachLine.lower().find(sev[0].value) > 0:
            log['type'] = sev[0].value
            log['information'] = eachLine
            log['status'] = model.stsEnum.valid.value
            flag = True
        elif eachLine.lower().find(sev[1].value) > 0:
            log['type'] = sev[1].value
            log['information'] = eachLine
            log['status'] = model.stsEnum.valid.value
            flag = True
        elif eachLine.lower().find(sev[2].value) > 0:
            log['type'] = sev[2].value
            log['information'] = eachLine
            log['status'] = model.stsEnum.valid.value
            flag = True
        elif flag:
            dup = session.query(SQLClass.log).filter(
                and_(SQLClass.log.information == log['information'],
                     SQLClass.log.source == log['source'])).first()
            if dup:
                print "log id is:", dup.logid
                var_logid = dup.logid
            else:
                mdinfo = md5.new()
                mdinfo.update(log['information'])
                mdinfo = mdinfo.hexdigest()
                logitem = SQLClass.log(
                    information=log['information'],
                    error_type=log['type'],
                    source=log['source'],
                    status=log['status'],
                    md5=mdinfo)
                try:
                    session.add(logitem)
                    session.flush()
                    print "log id is:", logitem.logid
                    var_logid = logitem.logid
                    session.commit()
                except Exception as e:
                    session.rollback()
                    if e.message.find("Duplicate entry") < 0:
                        autotestlog.logger.error(e.message)
                flag = False
            if var_logid and var_sysosid:
                dup = session.query(SQLClass.log_system_os).filter(
                    and_(SQLClass.log_system_os.logid == var_logid,
                         SQLClass.log_system_os.systemosid ==
                         var_sysosid)).first()
                if dup:
                    print "Existed log system os id:", dup.log_osid
                else:
                    logos = SQLClass.log_system_os(
                        logid=var_logid, systemosid=var_sysosid)
                    try:
                        session.add(logos)
                        session.flush()
                        print "log system os id is:", logos.log_osid
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        if e.message.find("Duplicate entry") < 0:
                            autotestlog.logger.error(e.message)
        else:
            pass 
    fopen.close()


# handle RedHat log file - messages
def rhelmsgHandle(filename, session):
    global src, var_sysosid, sev
    flag = False
    var_logid = ''
    fopen = open(filename, 'r')
    data = fopen.read()
    lines = data.split('\n')
    log['source'] = src
    for eachLine in lines:
        eachLine = eachLine[eachLine.find('localhost'):]
        if eachLine.lower().find(sev[0].value) > 0:
            log['type'] = sev[0].value
            log['information'] = eachLine
            log['status'] = model.stsEnum.valid.value
            flag = True
        elif eachLine.lower().find(sev[1].value) > 0:
            log['type'] = sev[1].value
            log['information'] = eachLine
            log['status'] = model.stsEnum.valid.value
            flag = True
        elif eachLine.lower().find(sev[2].value) > 0:
            log['type'] = sev[2].value
            log['information'] = eachLine
            log['status'] = model.stsEnum.valid.value
            flag = True
        elif flag:
            dup = session.query(SQLClass.log).filter(
                and_(SQLClass.log.information == log['information'],
                     SQLClass.log.source == log['source'])).first()
            if dup:
                print "log id is:", dup.logid
                var_logid = dup.logid
            else:
                mdinfo = md5.new()
                mdinfo.update(log['information'])
                mdinfo = mdinfo.hexdigest()
                logitem = SQLClass.log(
                    information=log['information'],
                    error_type=log['type'],
                    source=log['source'],
                    status=log['status'],
                    md5=mdinfo)
                try:
                    session.add(logitem)
                    session.flush()
                    print "log id is:", logitem.logid
                    var_logid = logitem.logid
                    session.commit()
                except Exception as e:
                    session.rollback()
                    if e.message.find("Duplicate entry") < 0:
                        autotestlog.logger.error(e.message)
                flag = False
            if var_logid and var_sysosid:
                dup = session.query(SQLClass.log_system_os).filter(
                    and_(SQLClass.log_system_os.logid == var_logid,
                         SQLClass.log_system_os.systemosid ==
                         var_sysosid)).first()
                if dup:
                    print "Existed log system os id:", dup.log_osid
                else:
                    logos = SQLClass.log_system_os(
                        logid=var_logid, systemosid=var_sysosid)
                    try:
                        session.add(logos)
                        session.flush()
                        print "log system os id is:", logos.log_osid
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        if e.message.find("Duplicate entry") < 0:
                            autotestlog.logger.error(e.message)
        else:
            pass
    fopen.close()


# handle SUSE log file - messages
def susemsgHandle(filename, session):
    global src, var_sysosid, sev
    var_logid = ''
    flag = False
    fopen = open(filename, 'r')
    data = fopen.read()
    lines = data.split('\n')
    log['source'] = src
    for eachLine in lines:
        eachLine = eachLine[eachLine.find('linux'):]
        if eachLine.lower().find(sev[0].value) > 0:
            log['type'] = sev[0].value
            log['information'] = eachLine
            log['status'] = model.stsEnum.valid.value
            flag = True
        elif eachLine.lower().find(sev[1].value) > 0:
            log['type'] = sev[1].value
            log['information'] = eachLine
            log['status'] = model.stsEnum.valid.value
            flag = True
        elif eachLine.lower().find(sev[2].value) > 0:
            log['type'] = sev[2].value
            log['information'] = eachLine
            log['status'] = model.stsEnum.valid.value
            flag = True
        elif flag:
            dup = session.query(SQLClass.log).filter(
                and_(SQLClass.log.information == log['information'],
                     SQLClass.log.source == log['source'])).first()
            if dup:
                print "log id is:", dup.logid
                var_logid = dup.logid
            else:
                mdinfo = md5.new()
                mdinfo.update(log['information'])
                mdinfo = mdinfo.hexdigest()
                logitem = SQLClass.log(
                    information=log['information'],
                    error_type=log['type'],
                    source=log['source'],
                    status=log['status'],
                    md5=mdinfo)
                try:
                    session.add(logitem)
                    session.flush()
                    print "log id is:", logitem.logid
                    var_logid = logitem.logid
                    session.commit()
                except Exception as e:
                    session.rollback()
                    if e.message.find("Duplicate entry") < 0:
                        autotestlog.logger.error(e.message)
                flag = False
            if var_logid and var_sysosid:
                dup = session.query(SQLClass.log_system_os).filter(
                    and_(SQLClass.log_system_os.logid == var_logid,
                         SQLClass.log_system_os.systemosid ==
                         var_sysosid)).first()
                if dup:
                    print "Existed log system os id:", dup.log_osid
                else:
                    logos = SQLClass.log_system_os(
                        logid=var_logid, systemosid=var_sysosid)
                    try:
                        session.add(logos)
                        session.flush()
                        print "log system os id is:", logos.log_osid
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        if e.message.find("Duplicate entry") < 0:
                            autotestlog.logger.error(e.message)
        else:
            pass
    fopen.close()


# logDB()
def logDB(param):
    global var_sysosid
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
    ret = checksysos(param['sysosid'], session)
    if ret != -1:
        rootdir = model.featureLogDir + param['logdir']
        ret = allFiles(rootdir, session)
        if ret != -1:
            return var_sysosid
        else:
            print "sysosid is not available."
    else:
        print "log handle error - var_sysosid is not available"
    session.close()
    engine.dispose()
    return -1


if __name__ == '__main__':
    param = {
        'sysosid': 14,
        'logdir': 'RedHat/7.5/log_20180326115359_sr630_RedHat_7.5'
    }
    logDB(param)
