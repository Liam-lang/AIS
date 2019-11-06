#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Dec 27, 2017
SQLClass.py: mysql database operational class using sqlalchemy
@author: Neo
Version: 1.0
'''
import sys
from sqlalchemy import *
from sqlalchemy.orm import *
from datetime import datetime

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")
from common import model

class user(model.Base):
    __tablename__ = 'user'
    __table_args__ = (Index('unique_constratint', "username", unique=True), )
    userid = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    firstname = Column(String(16), nullable=False)
    lastname = Column(String(16), nullable=False)
    username = Column(String(64), nullable=False)
    password = Column(String(64), nullable=False)
    histories = relationship('login_history', back_populates='rs_user')
    roles = relationship('role', back_populates='rs_user_role')

class role(model.Base):
    __tablename__ = 'role'
    roleid = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    userid = Column(
        Integer,
        ForeignKey('user.userid', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False)
    permission = Column(
        Enum(model.permitEnum), default=model.permitEnum.normal)
    rs_user_role = relationship('user', back_populates='roles')


class login_history(model.Base):
    __tablename__ = 'login_history'
    historyid = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    userid = Column(
        Integer,
        ForeignKey('user.userid', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False)
    history = Column(DateTime(), default=datetime.utcnow)
    rs_user = relationship('user', back_populates='histories')


class log_system_os(model.Base):
    __tablename__ = 'log_system_os'
    __table_args__ = (Index(
        'unique_constraint', "logid", "systemosid", unique=True), )
    log_osid = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    logid = Column(
        Integer,
        ForeignKey('log_table.logid', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False)
    systemosid = Column(
        Integer,
        ForeignKey(
            'system_os.system_osid', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False)
    rs_systemos = relationship('system_os', back_populates='logs')
    rs_log = relationship('log', back_populates='sysoses')


class log(model.Base):
    __tablename__ = 'log_table'
    __table_args__ = (Index('unique_constraint', "md5", unique=True), )
    logid = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    information = Column(BLOB, nullable=False)
    error_type = Column(Enum(model.typEnum), default=model.typEnum.error)
    source = Column(Enum(model.srcEnum), default=model.srcEnum.dmesg)
    status = Column(Enum(model.stsEnum), default=model.stsEnum.valid)
    comment = Column(BLOB)
    bznumber = Column(String(128))
    md5 = Column(String(64), nullable=False, unique=True)
    sysoses = relationship('log_system_os', back_populates='rs_log')


class system_os(model.Base):
    __tablename__ = 'system_os'
    __table_args__ = (Index('unique_constraint', "logfile", unique=True), )
    system_osid = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    systemid = Column(
        Integer,
        ForeignKey(
            'system_table.systemid', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False)
    osid = Column(
        Integer,
        ForeignKey('os_table.osid', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False)
    logfile = Column(String(128), nullable=False, unique=True)
    creation = Column(DateTime(), default=datetime.utcnow)
    tester = Column(String(64))
    engineer = Column(String(64))
    reportflag = Column(Enum(model.stsEnum), default=model.stsEnum.invalid)
    logs = relationship('log_system_os', back_populates='rs_systemos')
    rs_system = relationship('system', back_populates='os2')
    rs_os2 = relationship('os', back_populates='systems')


# os_table object:
class os(model.Base):
    # table name:
    __tablename__ = 'os_table'
    __table_args__ = (Index('unique_constraint', "imgname", unique=True), )
    # table structure:
    osid = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    name = Column(String(64), nullable=False)
    version = Column(String(64), nullable=False)
    imgname = Column(String(64), nullable=False)
    phase = Column(String(32))
    platform = Column(Enum(model.plmEnum), default=model.plmEnum.x86_64)
    driverflag = Column(Enum(model.stsEnum), default=model.stsEnum.invalid)
    md5 = Column(String(128), nullable=False, unique=True)
    systems = relationship('system_os', back_populates='rs_os2')


class driver(model.Base):
    __tablename__ = 'driver_table'
    __table_args__ = (Index(
        'unique_constraint', "location", "md5",
        unique=True), )
    driverid = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    name = Column(String(64), nullable=False)
    srcversion = Column(String(64), nullable=False)
    version = Column(String(64), nullable=False)
    vd = Column(Text, nullable=False)
    svsd = Column(Text)
    location = Column(String(256), nullable=False)
    rpmlocation = Column(String(256), nullable=False)
    modinfo = Column(BLOB, nullable=False)
    md5 = Column(String(64), nullable=False)
    osid = Column(
        String(256),
        nullable=False)


class system(model.Base):
    __tablename__ = 'system_table'
    __table_args__ = (Index(
        'unique_constraint', "model", "processor", "biosver", "biosmode", unique=True), )
    systemid = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    series = Column(Enum(model.srsEnum), default=model.srsEnum.thinksystem)
    biosmode = Column(Enum(model.modEnum), default=model.modEnum.UEFI)
    codename = Column(
        String(30),
        ForeignKey(
            'codename_table.codename', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True)
    model = Column(String(128), nullable=False)
    processor = Column(String(128), nullable=False)
    memory = Column(String(128))
    raid = Column(String(128))
    hba = Column(String(128))
    hdd = Column(String(128))
    biosver = Column(String(128))
    nic = Column(String(128))
    gpu = Column(String(128))
    os2 = relationship('system_os', back_populates='rs_system')
    rs_cdnm = relationship('codename', back_populates='rs_sys')


class codename(model.Base):
    __tablename__ = 'codename_table'
    __table_args__ = (Index('unique_constraint', "codename", unique=True), )
    id = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    codename = Column(String(32), nullable=False)
    model = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True)
    SS = Column(Date, nullable=False)
    rs_sys = relationship('system', back_populates='rs_cdnm')


class pciid(model.Base):
    __tablename__ = 'pciid_table'
    __table_args__ = (Index(
        'unique_constraint',
        "description",
        "vendorid",
        "deviceid",
        "subvendorid",
        "subdeviceid",
        unique=True), )
    pciidid = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    vendor = Column(String(64), nullable=False)
    description = Column(String(256), nullable=False)
    vendorid = Column(String(8), nullable=False)
    deviceid = Column(String(8), nullable=False)
    subvendorid = Column(String(8), nullable=False)
    subdeviceid = Column(String(8), nullable=False)
    project = Column(String(256), nullable=False)
    status = Column(Enum(model.stsEnum), default=model.stsEnum.valid)
    drivername = Column(String(256), nullable=True)
    driverversion = Column(String(64))


class testcase(model.Base):
    __tablename__ = 'testcase'
    tcid = Column(Integer, primary_key=True, nullable=False, unique=True)
    description = Column(String(128), nullable=False)
    bznumber = Column(String(128), nullable=False)
    platform = Column(String(128), nullable=False)


class pciresult(model.Base):
    __tablename__ = 'pciresult'
    __table_args__ = (Index(
        'unique_constraint', "description", "vendordevice", unique=True), )
    no = Column(Integer, primary_key=True, nullable=False, unique=True)
    vendor = Column(String(64), nullable=False)
    description = Column(String(256), nullable=False)
    vendordevice = Column(String(16), nullable=False, primary_key=True)
    project = Column(String(256), nullable=False)
    exists = Column(Enum(model.estEnum), default=model.estEnum.exist)
    updrvname = Column(String(256))
    updrvversion = Column(String(64))
    drivername = Column(String(256))
    driverversion = Column(String(64))


class logresult(model.Base):
    __tablename__ = 'logresult'
    no = Column(Integer, primary_key=True, nullable=False, unique=True)
    information = Column(BLOB, nullable=False)
    error_type = Column(Enum(model.typEnum), default=model.typEnum.error)
    source = Column(Enum(model.srcEnum), default=model.srcEnum.dmesg)
    logfile = Column(String(128), nullable=False)
    bznumber = Column(String(128))


class report(model.Base):
    __tablename__ = 'report'
    no = Column(Integer, primary_key=True, nullable=False, unique=True)
    # test case name
    tcname = Column(String(64), nullable=False)
    status = Column(Enum(model.rpEnum), default=model.rpEnum.Pass)
    message = Column(BLOB)
    logfile = Column(String(128))
    bznumber = Column(String(128))
    comment = Column(String(64))


class controlserver(model.Base):
    __tablename__ = 'controlserver_table'
    controlserverid = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    servername = Column(String(256), nullable=False)
    pubIPaddress = Column(String(256), nullable=False, unique=True)
    priIPaddress = Column(String(256), nullable=False)
    MACaddress = Column(String(256), nullable=False)
    location = Column(String(256), nullable=False)


class task(model.Base):
    __tablename__ = 'task_table'
    taskid = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    taskType = Column(String(16), nullable=False)
    testerName = Column(String(16), nullable=False)
    crlServer = Column(String(16), nullable=False)
    sutMACaddress = Column(String(32))
    MTSN = Column(String(32))
    OSVersion = Column(String(32), nullable=False)
    OSImage = Column(String(64), nullable=False)
    kernelPKG = Column(String(64))
    status = Column(Integer)

