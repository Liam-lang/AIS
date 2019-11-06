#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 09, 2018
model.py: sqlalchemy model file
@author: Neo
Version: 1.0
'''
import enum
import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import *
from hashlib import md5

dirDataServer="/srv/www/htdocs/DataServer"

#platform enum:
class plmEnum(enum.Enum):
    x86_64 = 'x86_64'
    i386 = 'i386'
    i686 = 'i686'


#series enum:
class srsEnum(enum.Enum):
    thinkserver = 'thinkserver'
    systemx = 'systemx'
    thinksystem = 'thinksystem'


#type enum:
class typEnum(enum.Enum):
    error = 'error'
    warning = 'warning'
    fail = 'fail'


#source enum:
class srcEnum(enum.Enum):
    dmesg = 'dmesg'
    messages = 'messages'
    mcelog = 'mcelog'
    x11 = 'x11'
    anaconda = 'anaconda'
    yast = 'yast'


#status enum:
class stsEnum(enum.Enum):
    valid = 'valid'
    invalid = 'invalid'


#isexist enum:
class estEnum(enum.Enum):
    exist = 'exist'
    NA = 'NA'


#bios mode enum:
class modEnum(enum.Enum):
    UEFI = 'UEFI'
    Legacy = 'Legacy'


#testcase status
class rpEnum(enum.Enum):
    Pass = 'Pass'
    Fail = 'Fail'


class permitEnum(enum.Enum):
    admin = '0'
    normal = '1'

class cfgEnum:
    MAC = '<<MAC>>'
    MTSN = '<<MTSN>>'
    SERVER_IP = '<<SERVER_IP>>'
    OS_VERSION = '<<OS_VERSION>>'
    TEST_CASE = '<<TEST_CASE>>'
    OS_IMAGE = '<<OS_IMAGE>>'
    KER_RPM = '<<KER_RPM>>'


#find the Nth occurred substring position in the string
def findSubstring(string, substring, times):
    current = 0
    for i in range(1, times + 1):
        current = string.find(substring, current) + 1
        if current == 0:
            return -1
    return current - 1

# calculate the md5 of the file 
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

#base class for creating class
Base = declarative_base()

#statusDir is used as a monitoring directory, cannot contain /,
# otherwise it is impossible to monitor file changes in subdirectories
statusDir = "/var/opt/lenovo/AIS/collect/status"
driverDir = "/var/opt/lenovo/AIS/collect/drivers/"
featureLogDir = "/var/opt/lenovo/AIS/collect/log/"
pciidDir = "/var/opt/lenovo/AIS/checkbase/PCIID/"
tmpDir = "/var/opt/lenovo/AIS/tmp/"
logDir = "/var/opt/lenovo/AIS/log/"
confDir = "/etc/opt/lenovo/AIS/conf/task"
RET_FAILED = -1
RET_SUCCESS = 0


#when you change database ,also change database4Dev as well.
#database4Dev = "ais.labs.lenovo.com"
#database4Dev = "10.245.100.27"
database4Dev = "10.245.100.28"

DBInstance ={'session':"",'engine':""}

#connect to the database
def connectDB(dbname):
    if dbname == "":
        dbname = "test"
    print "Create database"
    engine = create_engine(
        "mysql+mysqlconnector://root:AIS.lenovo1@"+database4Dev+":3306/")
    try:
        engine.execute("CREATE DATABASE "+dbname);
    except:
        print "DB exists"
    engine.dispose()
    engine = create_engine(
        "mysql+mysqlconnector://root:AIS.lenovo1@"+database4Dev+"/"+dbname,
        max_overflow=5,
        pool_size=30,
        pool_recycle=3600,
        echo=True)
    print "Done."
    return engine

def createDBInstance(DBname):
    DBInstance['engine'] = connectDB(DBname)
    print "Create database session..."
    DBSession = sessionmaker(bind=DBInstance['engine'])
    DBInstance['session'] = DBSession()
    print "Done."
    print "Create metadata object..."
    meta = MetaData(bind=DBInstance['engine'])
    meta.reflect(bind=DBInstance['engine'])
    Base.metadata.create_all(DBInstance['engine'] , checkfirst=True)
    print "Done."
    return DBInstance

def disconnectDB(DBInstance):
    DBInstance['session'].close()
    DBInstance['engine'].dispose()
    print "session is closed."

def getImgTask(driverFileName):
    underLine_index = driverFileName.rfind("_")
    taskId_index = driverFileName.rfind(".")
    imgName = driverFileName[0:underLine_index]
    taskID = driverFileName[underLine_index + 1:taskId_index]
    return imgName,taskID
