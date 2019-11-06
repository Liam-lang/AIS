#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 09, 2018
driver.py: handle the driver information under
model.driverDir/OSVs/version/**.txt
@author: Neo
Version: 1.0
'''
import sys, os, md5, getopt
reload(sys)
sys.setdefaultencoding('utf-8')
from sqlalchemy import *

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")
from sqlserver import SQLClass
from common import rdgenerator, autotestlog, model

# global variables
osname = ''
osversion = ''

DBname = "Linux"
DBInstance ={'session':"",'engine':""}


def addEntry2DriverTbl(completFlag, OSID, session):
    global driver, accumulateFlag

    if accumulateFlag & completFlag == completFlag:
        mdobj = md5.new()
        mdobj.update(driver['vd'])
        mdobj = mdobj.hexdigest()
        flag = session.query(SQLClass.driver).filter(
            and_(SQLClass.driver.md5 == mdobj,
                 SQLClass.driver.name == driver['name'],
                 SQLClass.driver.srcversion == driver[
                     'srcversion'])).first()
        if flag:
            print "Dirver already exists", flag.driverid
            osidArry = flag.osid.split(",")
            if str(OSID) not in osidArry:
                flag.osid = flag.osid + "," + str(OSID)
                try:
                    session.flush()
                    session.commit()
                except Exception as e:
                    session.rollback()
                    print "change osid is failed."
                    print e.message
        else:
            driveritem = SQLClass.driver(
                name=driver['name'],
                version=driver['version'],
                vd=driver['vd'],
                svsd=driver['svsd'],
                location=driver['location'],
                rpmlocation=driver['rpmlocation'],
                modinfo=driver['modinfo'],
                srcversion=driver['srcversion'],
                md5=mdobj,
                osid=OSID)
            try:
                session.add(driveritem)
                session.flush()
                print "driver id is:", driveritem.driverid
                session.commit()
            except Exception as e:
                session.rollback()
                if e.message.find("Duplicate entry") < 0:
                    autotestlog.logger.error(e.message)

        driver['name'] = ''
        driver['version'] = ''
        driver['vd'] = ''
        driver['svsd'] = ''
        driver['location'] = ''
        driver['rpmlocation'] = ''
        driver['modinfo'] = ''
        driver['srcversion'] = ''
        driver['rpmpackage'] = ''
        accumulateFlag = 0b0000

#handle pciid file
def driverHandle(filename, session, imgName):
    global osname,driver,accumulateFlag
    extko = "===>driverFile"
    extpci = "===>pciid"
    extinfo = "===>modinfo"
    extrpm = "===>RPM"
    extname = "/"
    extsrcver = "srcversion"
    extver = "version"
    extlib = "lib"
    # 1000 : RPM line has excueted  0010 : ko , 0100 : pciid 0001 : modinfo
    accumulateFlag = 0b0000
    # entry is completed, it's mean include ko,pciid,modinfo,RPM(linux only)
    completFlag = 0b1111
    #1000 : RPM line being excueted  0010 : ko , 0100 : pciid 0001 : modinfo
    flag = 0b0000

    #driver dictionary
    driver = {
        'name': '',
        'version': '',
        'srcversion': '',
        'vd': '',
        'svsd': '',
        'location': '',
        'rpmlocation': '',
        'modinfo': '',
        'rpmpackage':''
    }

    if osname.lower().find("vmware") != -1:
        completFlag = 0b0111

    print "driverHandle start.\n"
    try:
        queryEntry = session.query(
        SQLClass.os).filter(SQLClass.os.imgname == imgName).first()
    except Exception as e:
        print "error accurred when query os table.\n"
        print e.message
        return model.RET_FAILED
    if queryEntry:
        var_osid = queryEntry.osid
        print "osid exist in the OS table.\n"
    else:
        print "Update driver table failed with no OS item found in the OS table.\n"
        return model.RET_FAILED

    fopen = open(filename, 'r')
    print "filename is " + filename
    lines = fopen.readlines()
    print "open file is ok."
    for eachLine in lines:
        #print "eachLine is " + eachLine
        eachLine = eachLine.strip('\n')
        if eachLine.find(extko) >= 0:
            addEntry2DriverTbl(completFlag, var_osid, session)
            flag = 0b0010
            continue
        elif eachLine.find(extpci) >= 0:
            addEntry2DriverTbl(completFlag, var_osid, session)
            flag = 0b0100
            continue
        elif eachLine.find(extinfo) >= 0:
            addEntry2DriverTbl(completFlag, var_osid, session)
            flag = 0b0001
            continue
        elif eachLine.find(extrpm) >= 0:
            addEntry2DriverTbl(completFlag, var_osid, session)
            flag = 0b1000
            continue
        elif flag & 0b0010 == 0b0010:
            nPos = eachLine.rfind(extname)
            mPos = eachLine.find(extlib)
            driver['name'] = eachLine[nPos + 1:]
            if mPos != -1:
                driver['location'] = eachLine[mPos:]
            else:
                driver['location'] = eachLine
            accumulateFlag = accumulateFlag | 0b0010
        elif flag & 0b0100 == 0b0100:
            data = eachLine.split("::")
            if len(data) >= 2:
                if data[0] != '*:*':
                    driver['vd'] = driver['vd'] + data[0] +','
                driver['svsd'] = driver['svsd'] + data[1] + ','
            accumulateFlag = accumulateFlag | 0b0100
        elif flag & 0b0001 == 0b0001:
            keyVal = eachLine.split(":", 1)
            if keyVal[0].strip().lower() == extsrcver:
                driver['srcversion'] = keyVal[1].strip()
            if keyVal[0].strip().lower() == extver:
                driver['version'] = keyVal[1].strip()
            driver['modinfo'] = driver['modinfo'] + eachLine + '\n'
            accumulateFlag = accumulateFlag | 0b0001
        elif flag & 0b1000 == 0b1000:
            driver['rpmpackage'] = eachLine
            accumulateFlag = accumulateFlag | 0b1000
        else:
            print "Error: should check your condition"

    addEntry2DriverTbl(completFlag, var_osid, session)
    fopen.close()
    return model.RET_SUCCESS

# 递归遍历指定目录，显示目录下的所有文件名
def allFiles(rootdir, session, imgName, taskID):
    suffix = '.txt'
    ret = model.RET_FAILED
    list_dirs = os.walk(rootdir)
    for root, dirs, files in list_dirs:
        for fileName in files:
            filePath = os.path.join(root, fileName)
            #check if the file name ends in ".txt"
            if fileName.endswith(suffix):
                #get imgname from file name
                _imgName,_taskID = model.getImgTask(fileName)
                if _imgName != str(imgName) or _taskID != str(taskID) :
                    print "This is not the correct driver file,Because the current imgName is %s,taskID is %s \n" %(_imgName,_taskID)
                    continue

                #根据txt文件内容更新driver_table
                ret = driverHandle(filePath, session, imgName)

                #根据driver_table内容更新pciid_table的部分值
                #if _imgName.find("kernel") >= 0:
                #    kernelHandle(_imgName, session)

                nPos = fileName.index(suffix)
                rd = rdgenerator.id_generator()
                newname = fileName[0:nPos + 1] + rd
                os.rename(filePath, os.path.join(root, newname))
                return ret
    return ret

#driverDB()
#param example:kernel/4.18.20; RedHat/8.0;
#imgName example :kernel-5.2.1-1.x86_64.rpm
def driverDB(param, imgName, taskID):
    global osname

    print "param is " + param + "\n"
    osname, osversion = param.split('/')
    rootdir = model.driverDir + param
    print "osname is " + osname
    print "osversion is " + osversion
    print "rootdir is " + rootdir

    DBInstance = model.createDBInstance(DBname)
    ret = allFiles(rootdir, DBInstance['session'], imgName, taskID)
    model.disconnectDB(DBInstance)
    return ret


#print help information
def usage():
    print "usage: {0} [OPTS]".format(os.path.basename(__file__))
    print "  -d, --directory <driver information directory>\
           Store the driver information in the database"

    print "  -h, --help		Print this help message"


#read arguments
def main(argv):
    if argv:
        try:
            opts, args = getopt.getopt(argv, "hvd:", ["directory="])
        except getopt.GetoptError as err:
            print str(err)
            sys.exit(2)
        drv_dir = None
        verbose = False
        for opt, arg in opts:
            if opt == '-v':
                verbose = True
            elif opt in ("-d", "--directory"):
                drv_dir = arg
                return drv_dir
            elif opt in ("-h", "--help"):
                usage()
                sys.exit()
            else:
                assert False, "unhandled option"
                print "OK verbose=%s , driver directory is %s" % (str(verbose),
                                                                  drv_dir)
    else:
        usage()
        sys.exit(2)


if __name__ == '__main__':
    drvDir = main(sys.argv[1:])
    #imgName = "kernel-5.2.1-1.x86_64.rpm"
    imgName = "RHEL-8.1.0-20190508.0-x86_64-dvd1.iso"
    taskID = "125"
    if drvDir:
        driverDB(drvDir, imgName, taskID)
    else:
        print "Error input parameter!"
        usage()
        sys.exit(2)
