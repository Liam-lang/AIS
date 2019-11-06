#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 18, 2018
toexcel.py: dump table to excel
@author: Neo
Version: 1.0
'''
from sqlalchemy.inspection import inspect


#convert alchemy pci object to list which incluing enum type
def query_pci(rset):
    result = []
    for row in range(len(rset)):
        instance = inspect(rset[row])
        items = instance.attrs.items()
        result.append([])
        for col in range(len(items)):
            tmp = items[col][1].value
            if col == 2:
                tmp = tmp.value
            result[row].append(tmp)
    return instance.attrs.keys(), result


#convert alchemy log object to list which incluing enum type
def query_log(rset):
    result = []
    header = [
        'information', 'no', 'error type', 'bugzilla number', 'error source',
        'log file'
    ]
    for row in range(len(rset)):
        instance = inspect(rset[row])
        items = instance.attrs.items()
        result.append([])
        for col in range(len(items)):
            tmp = items[col][1].value
            if col == 2 or col == 4:
                tmp = tmp.value
            result[row].append(tmp)
    return header, result


#convert alchemy report object to list
def query_to_list(rset):
    result = []
    header = [
        'status', 'comment', 'no', 'testcase name', 'bugzilla number',
        'error message', 'log file'
    ]
    for row in range(len(rset)):
        instance = inspect(rset[row])
        items = instance.attrs.items()
        result.append([])
        for col in range(len(items)):
            tmp = items[col][1].value
            if col == 0:
                tmp = tmp.value
            result[row].append(tmp)
    return header, result


#convert testcase object to list
def tc_to_list(rset):
    result = []
    header = ['NO', 'Test Case']
    for row in range(len(rset)):
        instance = inspect(rset[row])
        items = instance.attrs.items()
        result.append([])
        for col in range(2):
            tmp = items[col][1].value
            result[row].append(tmp)
    return header, result


if __name__ == '__main__':
    print "hello"
