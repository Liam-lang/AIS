#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 09, 2018
testclass.py: sqlalchemy testing class
@author: Neo
'''
import sys
from sqlalchemy import *
from datetime import datetime

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")
from common import model
from analyze import report

class Test(model.Base):
    __tablename__ = 'test_table'
    __table_args__ = (Index('unique_key_val', "key", "val", unique=True), )
    id = Column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True)
    key = Column(String(30), nullable=False)
    val = Column(String(60))
    information = Column(Text, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

def case():
    print "start"
    report.testReport(36)
    print "end"

def case2():
    print "start"
    print "end"

if __name__ == "__main__":
    case()
