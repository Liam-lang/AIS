#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2017-12-26
sql-test.py: sql operaton interface testing function
@author: Neo
'''
import sys
import SQLHelper as sql

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")

def showTables():
    ret = sql.GetCommand("show tables")
    if len(ret) == 0:
        print "No table found!"
    else:
        for table in ret:
            print table
    return ret


def showInformation(tablename):
    cmd = "select * from %s" % tablename
    ret = sql.GetCommand(cmd)
    if len(ret) == 0:
        print "No information found in %s" % (tablename)
    else:
        for item in ret:
            print item
    return ret


def createTable():
    cmd = "create table test_table(nid int not null \
            auto_increment primary key, num int null)"

    ret = sql.GetCommand(cmd)
    print ret


def dropTable():
    cmd = "drop table test_table"
    ret = sql.GetCommand(cmd)
    print ret


if __name__ == "__main__":
    createTable()
    dropTable()
    tables = showTables()
    for table in tables:
        print "\nTable Name: %s" % table
        showInformation(table)
