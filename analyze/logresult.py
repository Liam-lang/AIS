#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 17, 2018
logresult.py: Get the log analyze report.
@author: Neo
Version: 1.0
'''
import os, sys, getopt
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")
from sqlserver import SQLClass
from common import autotestlog, model


#check if the input is right
def check(var_sysosid, session):
    flag = session.query(SQLClass.system_os).filter(
        SQLClass.system_os.system_osid == var_sysosid).first()
    if flag:
        return flag.system_osid
    else:
        return -1


#get the analyzed pci information in the database
def getresult(var_sysosid, session):
    print "getresult() in logresult start."
    count = 0
    #Clear the logresult table
    try:
        session.query(SQLClass.logresult).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        autotestlog.logger.error(e.message)
    #Get the right os based drivers
    logs = session.query(SQLClass.log_system_os).filter(
        SQLClass.log_system_os.systemosid == var_sysosid).all()
    logfileobj = session.query(SQLClass.system_os).filter(
        SQLClass.system_os.system_osid == var_sysosid).first()
    sPos = model.findSubstring(logfileobj.logfile, '_', 1)
    ePos = model.findSubstring(logfileobj.logfile, '_', 2)
    excelfile = '/log_result' + logfileobj.logfile[sPos:ePos] + '.xlsx'
    #Get the log information
    status = model.stsEnum.invalid.value
    for item in logs:
        count += 1
        tmp = session.query(SQLClass.log).filter(
            and_(SQLClass.log.logid == item.logid,
                 SQLClass.log.status != status)).first()
        if tmp:
            row = SQLClass.logresult(
                no=count,
                information=tmp.information,
                error_type=tmp.error_type,
                source=tmp.source,
                logfile=logfileobj.logfile,
                bznumber=tmp.bznumber)
            try:
                session.add(row)
                session.commit()
            except Exception as e:
                session.rollback()
                if e.message.find("Duplicate entry") < 0:
                    autotestlog.logger.error(e.message)
        else:
            pass

#print help information
def usage():
    print "usage: {0} [OPTS]".format(os.path.basename(__file__))
    print "  -i, --id <system_os id>	\
            Output the pciid result for the specified system_os id"

    print "  -h, --help					Print this help message"


def main(argv):
    if argv:
        try:
            opts, args = getopt.getopt(argv, "hvi:", ["system_osid="])
        except getopt.GetoptError as err:
            print str(err)
            sys.exit(2)
        var_sysosid = None
        verbose = False
        for opt, arg in opts:
            if opt == '-v':
                verbose = True
            elif opt in ("-i", "--system_osid"):
                var_sysosid = arg
                return var_sysosid
            elif opt in ("-h", "--help"):
                usage()
                sys.exit()
            else:
                assert False, "unhandled option"
                print "Verbose value is %s, the system_osid is %d" % (
                    str(verbose), var_sysosid)
    else:
        usage()
        sys.exit(2)


#logAnalyze()
def logAnalyze(ret):
    if ret:
        #connect to the database
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

        flag = check(ret, session)
        if flag != -1:
            getresult(flag, session)
        else:
            print "Please input the right parameter!"
        session.close()
        engine.dispose()
    else:
        print "Error input parameter!"
        usage()
        sys.exit(2)


if __name__ == '__main__':
    ret = main(sys.argv[1:])
    logAnalyze(ret)
