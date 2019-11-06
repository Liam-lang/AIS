#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2018-01-05
SQLClassclass-test.py: SQLClassclass operation interface testing function
@author: Neo
'''

import sys, enum
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")
from common import model
from sqlserver import SQLClass
import testclass

engine = create_engine(
    'mySQLClass+mySQLClassconnector://root:AIS.lenovo1@ais.labs.lenovo.com:3306/test',
    echo=True)
print "Create database session:"
DBSession = sessionmaker(bind=engine)
session = DBSession()
print "Create metadata object:"
meta = MetaData(bind=engine)
meta.reflect(bind=engine)


class sexEnum(enum.Enum):
    female = 'female'
    male = 'male'


def initDB():
    if 'Table_1' in meta.tables:
        meta.tables['Table_1'].drop()
    if 'Table_2' in meta.tables:
        meta.tables['Table_2'].drop()
    if 'Table_3' in meta.tables:
        meta.tables['Table_3'].drop()
    if 'Table_4' in meta.tables:
        meta.tables['Table_4'].drop()
    if 'test_table' in meta.tables:
        meta.tables['test_table'].drop()
    else:
        print "No tables found in the Database."
    print "Create tables based on class:"
    model.Base.metadata.create_all(engine, checkfirst=True)
    print "Add rows in the testclass.Test:"
    testers = [
        testclass.Test(
            key='tester1',
            val='hello, tester1!',
            information="hello, I am the first very very very long long text.\
            I want to tell you a long long story.",
            date=datetime(2018, 01, 8)),
        testclass.Test(
            key='tester2',
            val='hello, tester2!',
            information="hello, I am the second very very very long long text.\
            I want to tell you a long long story.",
            date=datetime(2018, 1, 8)),
        testclass.Test(
            key='tester3',
            val='hello, tester3!',
            information="hello, I am the third very very very long long text.\
            I want to tell you a long long story.",
            date=datetime(2018, 01, 8)),
        testclass.Test(
            key='tester4',
            val='hello, tester2!',
            information="hello, I am the fourth very very very long long text.\
            I want to tell you a long long story.")
    ]
    session.add_all(testers)
    session.commit()


def showTable():
    for table in meta.sorted_tables:
        print table


def createOneTable():
    if not 'Table_1' in meta.tables:
        t1 = Table('Table_1', meta,
                   Column('id', Integer, primary_key=True, autoincrement=True),
                   Column('name', String(20)))
        t1.create()
    else:
        return


def createTables():
    if 'Table_2' not in meta.tables:
        t2 = Table('Table_2', meta,
                   Column('id', Integer, primary_key=True, autoincrement=True),
                   Column('sex', Enum(sexEnum)))
        t3 = Table('Table_3', meta,
                   Column('id', Integer, primary_key=True, autoincrement=True),
                   Column('age', Integer))
        meta.create_all()
    else:
        return


def dropTable():
    if 'Table_1' in meta.tables:
        meta.tables['Table_1'].drop()
    if 'Table_2' in meta.tables:
        meta.tables['Table_2'].drop()
    if 'Table_3' in meta.tables:
        meta.tables['Table_3'].drop()


def insertObj():
    if 'Table_4' not in meta.tables:
        table4 = Table('Table_4', meta,
                       Column(
                           'id', Integer, primary_key=True,
                           autoincrement=True), Column('sex', Enum(sexEnum)))
        table4.create()
    table = meta.tables['Table_4']
    ins = table.insert().values(sex='male')
    conn = engine.connect()
    conn.execute(ins)
    conn.execute(table.insert(), [{'sex': 'female'}, {'sex': 'male'}])


def queryObj():
    print "----> order_by(id):"
    row = session.query(testclass.Test).order_by(testclass.Test.id)
    for _row in row.all():
        print _row.key, _row.val, _row.information, _row.date

    print "\n----> order_by(desc(id)):"
    row = session.query(testclass.Test).order_by(desc(testclass.Test.id))
    for _row in row.all():
        print _row.key, _row.val, _row.information, _row.date

    print "\n----> order_by(date):"
    row = session.query(testclass.Test).order_by(testclass.Test.date)
    for _row in row.all():
        print _row.key, _row.val, _row.information, _row.date

    print "\n----> EQUAL:"
    row = session.query(testclass.Test).filter(testclass.Test.id == 2)
    _row = row.first()
    print _row.key, _row.val, _row.information, _row.date

    print "\n----> NOT EQUAL:"
    row = session.query(testclass.Test).filter(testclass.Test.id != 2)
    for _row in row.all():
        print _row.key, _row.val, _row.information, _row.date

    print "\n----> IN:"
    row = session.query(testclass.Test).filter(
        testclass.Test.key.in_(['tester1', 'tester2']))
    for _row in row.all():
        print _row.key, _row.val, _row.information, _row.date

    print "\n----> NOT IN:"
    row = session.query(
        testclass.Test).filter(~testclass.Test.key.in_(['tester1', 'tester2']))
    for _row in row.all():
        print _row.key, _row.val, _row.information, _row.date

    print "\n----> AND:"
    row = session.query(
        testclass.Test).filter(testclass.Test.key == 'tester1',
                               testclass.Test.val == 'hello, tester1!')
    _row = row.first()
    print _row.key, _row.val, _row.information, _row.date

    print "\n----> OR:"
    row = session.query(testclass.Test).filter(
        or_(testclass.Test.key == 'tester1', testclass.Test.key == 'tester2'))
    for _row in row.all():
        print _row.key, _row.val, _row.information, _row.date

    print "\n----> NULL:"
    row = session.query(testclass.Test).filter(testclass.Test.date == None)
    for _row in row.all():
        print _row.key, _row.value, _row.information

    print "\n----> NOT NULL:"
    row = session.query(testclass.Test).filter(testclass.Test.date != None)
    for _row in row.all():
        print _row.key, _row.val, _row.information, _row.date

    print "\n----> LIKE"
    row = session.query(testclass.Test).filter(
        testclass.Test.id.like('%%ster1%'))
    for _row in row.all():
        print _row.key, _row.val, _row.information, _row.date


def delObj():
    row = session.query(
        testclass.Test).filter(testclass.Test.key == 'tester1').first()
    print row
    session.delete(row)
    session.commit()
    row = session.query(testclass.Test).filter(testclass.Test.key == 'tester1')
    print row.all()


def updateObj():
    row = session.query(
        testclass.Test).filter(testclass.Test.key == 'tester2').first()
    print "original:", row.val
    row.val = ""
    session.commit()
    row = session.query(
        testclass.Test).filter(testclass.Test.key == 'tester2').first()
    print "updated:", row.val


def repeatchk():
    reptester3 = testclass.Test(
        key="tester3",
        val="hello, tester3!",
        information="hello, I am the fifth very very very long long text. \
        I want to tell you a long long story.")
    try:
        session.add(reptester3)
        session.commit()
    except Exception as e:
        print e
        session.rollback()


def foreignchk():
    testos = SQLClass.os(
        name="testos",
        version="1.0",
        phase="beta",
        platform="x86_64",
        imgname="testos.iso")
    try:
        session.add(testos)
        session.commit()
    except Exception as e:
        print e
        session.rollback()
    osrow = session.query(
        SQLClass.os).filter(SQLClass.os.name == 'testos').first()
    print "testos id of testos:", osrow.osid
    systemrow = session.query(
        SQLClass.system).filter(SQLClass.system.model == 'rs140').first()
    print "system id of rs140:", systemrow.systemid
    test_system_os = SQLClass.system_os(
        systemid=systemrow.systemid,
        osid=osrow.osid,
        logfile="/home/information/log/")
    try:
        session.add(test_system_os)
        session.commit()
    except Exception as e:
        print e
        session.rollback()
    print "Foreignkey --> on update:"
    osrow.version = "1.1"
    session.commit()
    print "Foreignkey --> on delete:"
    session.delete(osrow)
    session.commit()
    row = session.query(SQLClass.system_os).order_by(
        SQLClass.system_os.system_osid)
    for _row in row.all():
        print _row.system_osid, _row.systemid, _row.osid, _row.logfile


#def rollback():
#	session.add(row)
#	session.rollback()

if __name__ == "__main__":

    print "Init database..."
    initDB()
    print "Fundamental testing..."
    print "Show all the tables:"
    showTable()

    print "Create one table called \"Table_1\""
    createOneTable()
    showTable()
    print "Create two more tables called \"Table_2\" and \"Table_3\""
    createTables()
    showTable()

    print "Drop the new created three tables:"
    dropTable()
    showTable()

    print "Insert Objects with core method:"
    insertObj()
    #Add rows in the testclass.Test table

    print "Query Objects:"
    queryObj()
    print "Delete tester1:"
    delObj()
    print "Update Objects:"
    updateObj()
    #rollback()
    #ORM method to operate table object
    print "Insert the same object:"
    repeatchk()
    print "Foreignkey function check:"
    foreignchk()
    print "ORM method to operate table object:"
    tester5 = testclass.Test(
        key='tester5',
        val='hello, tester5!',
        information='''blablabalabalablaalalallalalalall!@#''')
    try:
        session.add(tester5)
        session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()
    print "OS enablement database testing..."
    print "Create database session:"
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    session.close()

    engine.dispose()
