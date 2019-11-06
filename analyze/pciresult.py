#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 17, 2018
pciresult.py: Get the pciid analyzing report.
@author: Neo
Version: 1.0
'''
import os, sys, re, getopt
import pandas as pd
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
reload(sys)
sys.setdefaultencoding('utf-8')

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")
from sqlserver import SQLClass
from common import autotestlog, toexcel, model


#global variable
osdict = {
    'Red Hat Enterprise Linux Server': 'RedHat',
    'SUSE Enterprise Linux Server': 'SUSE',
    'Linux Upstream Kernel': 'kernel',
    'VMware': 'VMware'
}
DBname = "Linux"
DBInstance = {"session": "", "engine": ""}


#generate pciresult table in database from pciid_table and driver_table
def getPciresult(osID, kernelID, session, taskID):
    print "getPciresult() in pciresult start."
    count = 0
    #Clear the pciresult table
    try:
        session.query(SQLClass.pciresult).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        autotestlog.logger.error(e.message)
        return model.RET_FAILED
    print "clear pciresult table success. "

    #Get the pciid from BB team
    devices = session.query(SQLClass.pciid).filter(
        SQLClass.pciid.status == model.stsEnum.valid.value).all()
    if devices:
        for device in devices:
            count += 1
            isexist = model.estEnum.NA
            osDrvName = ''
            osDrvVer = ''
            kernelDrvName = ''
            kernelDrvVer = ''
            pciid = device.vendorid.strip() + ':' + device.deviceid.strip()
            pciidu = pciid.upper()
            pciidl = pciid.lower()
            #check if the device is supported in specific OS
            drvinfos = session.query(SQLClass.driver).filter(
                    or_(
                        SQLClass.driver.vd.contains(pciidu),
                        SQLClass.driver.vd.contains(pciidl))
                    ).all()
            if drvinfos:
                for drvinfo in drvinfos:
                    osidArry = drvinfo.osid.split(",")
                    if str(osID) in osidArry:
                        isexist = model.estEnum.exist
                        osDrvName = drvinfo.location
                        osDrvVer = drvinfo.version
                    if str(kernelID) in osidArry:
                        kernelDrvName = drvinfo.name
                        kernelDrvVer = drvinfo.version
            row = SQLClass.pciresult(
                no=count,
                vendor=device.vendor,
                description=device.description,
                vendordevice=pciid,
                project=device.project,
                exists=isexist,
                updrvname=kernelDrvName,
                updrvversion=kernelDrvVer,
                drivername=osDrvName,
                driverversion=osDrvVer)
            try:
                session.add(row)
                session.commit()
            except Exception as e:
                session.rollback()
                if e.message.find("Duplicate entry") < 0:
                    autotestlog.logger.error(e.message)
    else:
        print "NO device information found in the database"
        return model.RET_FAILED
    print "Add recored to pciresult success."
    return model.RET_SUCCESS


#append data to driverData
def appendData():
    global driverData, itemNum, entry, accumulateFlag, completFlag
    if accumulateFlag & completFlag == completFlag:
        driverData[itemNum].append(str(itemNum+1))
        driverData[itemNum].append(entry['stringko'])
        driverData[itemNum].append(entry['stringpci'])
        driverData[itemNum].append(entry['stringinfo'])
        driverData[itemNum].append(entry['stringrpm'])
        itemNum = itemNum + 1
        driverData.append([])
        entry['stringrpm'] = ""
        entry['stringko'] = ""
        entry['stringpci'] = ""
        entry['stringinfo'] = ""
        accumulateFlag = 0b0000

#read data from driver file
def readData(driverFile):
    global driverData, itemNum, entry,accumulateFlag,completFlag

    # array data readed from driver file
    driverData = [[]]
    # count of entry
    itemNum = 0
    # 1000 : RPM line has excueted  0010 : ko , 0100 : pciid 0001 : modinfo
    accumulateFlag = 0b0000
    # entry is completed, it's mean include ko,pciid,modinfo,RPM(linux only)
    completFlag = 0b1111
    #1000 : RPM line being excueted  0010 : ko , 0100 : pciid 0001 : modinfo
    flag = 0b0000
    extrpm = "===>RPM"
    extko = "===>driverFile"
    extpci = "===>pciid"
    extinfo = "===>modinfo"
    # content of entry
    entry = {
        'stringrpm': '',
        'stringko': '',
        'stringpci': '',
        'stringinfo': ''
    }

    print "name of driverFile is " + driverFile
    index = driverFile.rfind("/")
    if driverFile[index:].lower().find("vmware") != -1:
        completFlag = 0b0111
    fopen = open(driverFile, 'r')
    lines = fopen.readlines()
    print "open file is ok."
    for eachLine in lines:
        # print "eachLine is " + eachLine
        if eachLine.find(extrpm) >= 0:
            appendData()
            flag = 0b1000
            continue
        if eachLine.find(extko) >= 0:
            appendData()
            flag = 0b0010
            continue
        if eachLine.find(extpci) >= 0:
            appendData()
            flag = 0b0100
            continue
        if eachLine.find(extinfo) >= 0:
            appendData()
            flag = 0b0001
            continue
        if flag & 0b1000 == 0b1000:
            entry['stringrpm'] = entry['stringrpm'] + eachLine
            accumulateFlag = accumulateFlag | 0b1000
        if flag & 0b0010 == 0b0010:
            entry['stringko'] = entry['stringko'] + eachLine
            accumulateFlag = accumulateFlag | 0b0010
        if flag & 0b0100 == 0b0100:
            entry['stringpci'] = entry['stringpci'] + eachLine
            accumulateFlag = accumulateFlag | 0b0100
        if flag & 0b0001 == 0b0001:
            entry['stringinfo'] = entry['stringinfo'] + eachLine
            accumulateFlag = accumulateFlag | 0b0001
    appendData()
    return driverData

#create report
def createReport(osID, session, taskID):
    print "createReport() in pciresult start."

    #dump pciresult table information to excel
    result = session.query(SQLClass.pciresult).all()
    if result:
        osEntry = session.query(SQLClass.os).filter(SQLClass.os.osid == osID).first()
        osEntry.driverflag = model.stsEnum.valid.value
        osname = osdict[osEntry.name]
        osversion = osEntry.version.split("-",1)[0].split(".update",1)[0]

        try:
            session.commit()
            print "Change driverflag in os table success."
            #make report file name
            osDrvPath = model.driverDir + osname + '/' + osversion + '/'
            rstfilename = osDrvPath + osEntry.imgname[0:-4] + '_'+ taskID + '.xlsx'
            print "result file name is :" + rstfilename
            #make writer and define format
            writer = pd.ExcelWriter(rstfilename, engine='xlsxwriter')
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1,
                'font_name': 'Times New Roman'
            })
            cell_format = workbook.add_format()
            cell_format.set_border(1)
            cell_format.set_text_wrap()
            cell_format.set_font_name('Times New Roman')

            #prepare [Device Information]page data
            nameList = ["", "", "", "", OSImgName, "", kernelName, "", "", ""]
            key, data = toexcel.query_pci(result)
            df = pd.DataFrame(data, columns=key)
            #change data order
            df = df[[
                'no', 'vendor', 'description', 'vendordevice', 'drivername',
                'driverversion', 'updrvname', 'updrvversion', 'project', 'exists'
            ]]
            #write data to excel
            df.to_excel(
                writer,
                sheet_name='Device Information',
                startrow=2,
                index=False,
                header=False)
            #set format to excel
            di_worksheet = writer.sheets['Device Information']
            di_worksheet.set_column('A:A', 10)
            di_worksheet.set_column('B:B', 20)
            di_worksheet.set_column('C:C', 60)
            di_worksheet.set_column('D:D', 15)
            di_worksheet.set_column('E:E', 40)
            di_worksheet.set_column('F:F', 15)
            di_worksheet.set_column('G:G', 20)
            di_worksheet.set_column('H:H', 15)
            di_worksheet.set_column('I:I', 20)
            di_worksheet.set_column('J:J', 10)

            for col_num, value in enumerate(nameList):
                di_worksheet.write(0, col_num, value, header_format)
            for col_num, value in enumerate(df.columns.values):
                di_worksheet.write(1, col_num, value, header_format)
            for row, value in enumerate(df.values):
                for col in range(10):
                    di_worksheet.write(row + 2, col, value[col], cell_format)
            print "Write excel from pciresult table succese.\n"

            #prepare [os driver information]page data
            #read driver file and return data
            #data is like
            #[["1","2"],
            #["3","4"]]
            randomN = ""
            re_name = OSImgName + "_" + taskID + "." + "(\w+)"
            for dirpath, dirnames, filenames in os.walk(osDrvPath):
                for file in filenames:
                    filter_task = re.compile(re_name)
                    filter_id = filter_task.findall(file)
                    for suffix in filter_id:
                        if suffix != "repo" and suffix != "xlsx":
                            randomN = suffix
                            break
            if randomN :
                data = readData(osDrvPath + OSImgName + "_" + taskID + "." + randomN)
                if data != [[]]:
                    print "driver file content is not null."
                    key = ["no","driverFile","pciid","modinfo","RPM"]
                    df = pd.DataFrame(data, columns=key)
                    df.to_excel(
                        writer,
                        sheet_name='os driver information',
                        startrow=1,
                        index=False,
                        header=False)
                    di_worksheet = writer.sheets['os driver information']
                    di_worksheet.set_column('A:A', 5)
                    di_worksheet.set_column('B:B', 56)
                    di_worksheet.set_column('C:C', 16)
                    di_worksheet.set_column('D:D', 56)
                    di_worksheet.set_column('E:E', 56)
                    for col_num, value in enumerate(df.columns.values):
                        di_worksheet.write(0, col_num, value, header_format)
                    for row, value in enumerate(df.values):
                        for col in range(5):
                            di_worksheet.write(row + 1, col, value[col], cell_format)
            print "Write excel from os driver file succese.\n"

            #prepare [kernel driver information]page data
            #read driver file and return data
            randomN=""
            if kernelName :
                re_name = kernelName + "_" + taskID + "."+"(\w+)"
                kernelversion = kernelName.split("-",2)[1]
                kernelDrvPath = model.driverDir + "kernel" + '/' + kernelversion + '/'
                for dirpath, dirnames, filenames in os.walk(kernelDrvPath):
                    for file in filenames:
                        filter_task = re.compile(re_name)
                        filter_id = filter_task.findall(file)
                        for suffix in filter_id:
                            if suffix != "repo" and suffix != "xlsx":
                                randomN=suffix
                                break
            if randomN :
                data = readData(kernelDrvPath + kernelName + "_" + taskID + "." + randomN)
                if data != [[]]:
                    key = ["no","driverFile","pciid","modinfo","RPM"]
                    df = pd.DataFrame(data, columns=key)
                    df.to_excel(
                        writer,
                        sheet_name='kernel driver information',
                        startrow=1,
                        index=False,
                        header=False)

                    di_worksheet = writer.sheets['kernel driver information']
                    di_worksheet.set_column('A:A', 5)
                    di_worksheet.set_column('B:B', 56)
                    di_worksheet.set_column('C:C', 16)
                    di_worksheet.set_column('D:D', 56)
                    di_worksheet.set_column('E:E', 56)

                    for col_num, value in enumerate(df.columns.values):
                        di_worksheet.write(0, col_num, value, header_format)
                    for row, value in enumerate(df.values):
                        for col in range(5):
                            di_worksheet.write(row + 1, col, value[col], cell_format)
            print "Write excel from kernel driver file succese.\n"

            writer.save()
            workbook.close()
        except Exception as e:
            session.rollback()
            print "write report failed because :"
            print e
    else:
        return -1


#get kernelName and os name from task table
def findName(taskID, session):
    # imageFlag = -1
    # kernelFlag = -1
    imageName = ""
    kernelName = ""

    try:
        queryEntry = session.query(
        SQLClass.task).filter(SQLClass.task.taskid == taskID).first()
    except Exception as e:
        print "Update pciresult table failed with error accurred when query task table.\n"
        print e.message
        return imageName, kernelName
    if queryEntry:
        imageName = queryEntry.OSImage
        kernelName = queryEntry.kernelPKG
        print "task exist in the task table.os image name is %s , kernel pakege name is %s\n"%(imageName,kernelName)
        return imageName, kernelName
    else:
        print "Update pciresult table failed with no task item found in the task table.\n"
        return imageName, kernelName


#get imageID from os_table by imagename
def getOSID(var_imgname, session):
    try:
        queryEntry = session.query(
        SQLClass.os).filter(SQLClass.os.imgname == var_imgname).first()
    except Exception as e:
        print "error accurred when query os table.\n"
        print e.message
        return model.RET_FAILED
    if queryEntry:
        print "osid exist in the OS table.os id is\n",queryEntry.osid
        return queryEntry.osid
    else:
        print "Update driver table failed with no OS item found in the OS table.\n"
        return model.RET_FAILED


#create pciresult table and  report
def pciAnalyze(taskID):
    global OSImgName, kernelName
    print "pciAnalyze() start."

    DBInstance = model.createDBInstance(DBname)
    OSImgName, kernelName = findName(taskID, DBInstance['session'])
    print "kernel name is :" + kernelName
    print "os name is :" + OSImgName

    if OSImgName == "" and kernelName == "":
        model.disconnectDB(DBInstance)
        return model.RET_FAILED

    osID = getOSID(OSImgName, DBInstance['session'])
    if osID != model.RET_FAILED:
        kernelID = getOSID(kernelName, DBInstance['session'])
        ret = getPciresult(osID, kernelID, DBInstance['session'], taskID)
        if ret != model.RET_FAILED:
            createReport(osID, DBInstance['session'], taskID)
    else:
        print "Please input the right OS image name!"
    model.disconnectDB(DBInstance)


#print help information
def usage():
    print "usage: {0} [OPTS]".format(os.path.basename(__file__))
    print "  -t, --taskid <task id in task page>		\
            Output the pciid result for the specified task"

    print "  -h, --help							\
            print this help message"


#handle input parameter
def main(argv):
    if argv:
        var_taskid = None
        try:
            opts, _ = getopt.getopt(argv, 'ht:',
                                    ['help', 'taskid='])
        except getopt.GetoptError as err:
            print str(err)
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-t", "--taskid"):
                print "get task id is",arg
                var_taskid = arg
            elif opt in ("-h", "--help"):
                usage()
                sys.exit()
            else:
                print "unhandled option : %s" % opt
        return var_taskid
    else:
        usage()
        sys.exit(2)


#example : python pciresult.py -t taskID
if __name__ == '__main__':
    _taskID = main(sys.argv[1:])
    pciAnalyze(_taskID)

