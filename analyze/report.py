#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Feb 01, 2018
report.py: Get the testing report.
@author: Neo
Version: 1.0
'''
import os, sys, getopt, datetime
import pandas as pd
import logresult
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")
from sqlserver import SQLClass
from common import autotestlog, toexcel, model


#check if the input is right and the system_os exists
def check(var_sysosid, session):
    flag = session.query(SQLClass.system_os).filter(
        SQLClass.system_os.system_osid == var_sysosid).first()
    if flag:
        return flag.system_osid
    else:
        return -1

#get the analyzed pci information in the database
def getresult(var_sysosid, session):
    report = {
        'testcase name': '',
        'status': '',
        'bugzilla number': '',
        'error message': '',
        'log file': '',
        'comment': '',
        'tester': '',
        'engineer': ''
    }
    config_title = [
        'BIOS mode', 'Platform', 'Processor', 'Operating System', 'OS image',
        'Memory', 'RAID', 'HBA', 'HDD', 'BIOS/BMC version', 'NIC', 'GPU'
    ]
    configuration = []
    count = 0
    #Get the right system os information
    sysos_obj = session.query(SQLClass.system_os).filter(
        SQLClass.system_os.system_osid == var_sysosid).first()
    sys_obj = session.query(SQLClass.system).filter(
        SQLClass.system.systemid == sysos_obj.systemid).first()
    os_obj = session.query(
        SQLClass.os).filter(SQLClass.os.osid == sysos_obj.osid).first()
    if not sysos_obj or not sys_obj or not os_obj:
        print "sysos/sys/os objects check error"
        return
    #bios mode
    configuration.append(sys_obj.biosmode.value)
    #platform
    configuration.append(sys_obj.model)
    #processor
    configuration.append(sys_obj.processor)
    #os information
    configuration.append(os_obj.name + ' ' + os_obj.version)
    configuration.append(os_obj.imgname)
    # memory
    configuration.append(sys_obj.memory)
    # RAID
    configuration.append(sys_obj.raid)
    # HBA
    configuration.append(sys_obj.hba)
    # HDD
    configuration.append(sys_obj.hdd)
    # BIOS/BMC version
    configuration.append(sys_obj.biosver)
    # NIC
    configuration.append(sys_obj.nic)
    # GPU
    configuration.append(sys_obj.gpu)

    report['tester'] = sysos_obj.tester
    report['engineer'] = sysos_obj.engineer

    #Get the testcase status
    sPos = model.findSubstring(sysos_obj.logfile, '_', 1)
    ePos = model.findSubstring(sysos_obj.logfile, '_', 2)
    excelfile = 'report_' + sysos_obj.logfile[sPos + 1:ePos] + '.xlsx'
    tcresult_path = sysos_obj.logfile + '/report.txt'
    try:
        fopen = open(tcresult_path, 'r')
        lines = fopen.readlines()
        for line in lines:
            line = line.strip('\n')
            flag = False
            if line.lower().find("case") >= 0 and line.lower().find("fail") == -1:
                info = line.split(':')
                report['testcase name'] = info[0][5:]
                report['status'] = info[1]
                report['error message'] = "None"
                count += 1
                flag = True
            elif line.lower().find("case") >= 0 and line.lower().find("fail") >= 0:
                info = line.split(':')
                report['testcase name'] = info[0][5:]
                bz_obj = session.query(
                    SQLClass.testcase).filter(SQLClass.testcase.description == report['testcase name']).first()
                if(bz_obj):
                    report['bugzilla number'] = bz_obj.bznumber
                else:
                    print "Can't find the testcase:", report['testcase name']
                report['status'] = info[1]
                count += 1
                pass
            else:
                report['error message'] = line
                report[
                    'log file'] = "http://ais.labs.lenovo.com" + sysos_obj.logfile + '/' + \
                               report['testcase name'] + '/' + report['testcase name'] + ".txt"
                flag = True
            if flag:
                row = SQLClass.report(
                    no=count,
                    tcname=report['testcase name'],
                    status=report['status'],
                    message=report['error message'],
                    bznumber=report['bugzilla number'],
                    logfile=report['log file'])
                try:
                    session.add(row)
                    session.commit()
                    report['log file'] = ''
                except Exception as e:
                    session.rollback()
                    autotestlog.logger.error(e.message)
    except IOError:
        print "Testcase report.txt file open failed."
        return

# dump test report and log report table information to excel
    filename = sysos_obj.logfile + '/' + excelfile
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')
    # system config worksheet data
    sysconfig = {
        "configuration title": config_title,
        "configuration": configuration
    }
    config_df = pd.DataFrame(data=sysconfig)
    # test engineer information
    date_time = datetime.datetime.strptime(sysos_obj.logfile[sPos + 1:ePos],
                                           '%Y%m%d%H%M%S')
    tester_title = ['OS Engineer', 'OS Tester', 'Date']
    tester_info = [report['engineer'], report['tester'], str(date_time)]
    tester = {"tester title": tester_title, "tester information": tester_info}
    tester_df = pd.DataFrame(data=tester)
    # test case information
    tc_objs = session.query(SQLClass.testcase).all()
    if tc_objs:
        tc_key, tc_data = toexcel.tc_to_list(tc_objs)
        tc_df = pd.DataFrame(tc_data, columns=tc_key)
        tc_df = tc_df[['NO', 'Test Case']]
    else:
        message = "testcase list not found in database"
        autotestlog.logger.error(message)

    # Write Test Report data to workbook
    tc_df.to_excel(
        writer,
        sheet_name='Test Report',
        startrow=7,
        index=False,
        header=False)
    tester_df = tester_df[['tester title', 'tester information']]
    tester_df.to_excel(
        writer,
        sheet_name='Test Report',
        startrow=1,
        index=False,
        header=False)
    config_df = config_df[['configuration title', 'configuration']]
    config_df.to_excel(
        writer,
        sheet_name='Test Report',
        startrow=1,
        startcol=3,
        index=False,
        header=False)

    # Write Test Results data to workbook
    result = session.query(SQLClass.report).all()
    if result:
        sysos_obj.reportflag = model.stsEnum.valid.value
        try:
            session.commit()
            key, data = toexcel.query_to_list(result)
            result_df = pd.DataFrame(data, columns=key)
            result_df = result_df[[
                'no', 'testcase name', 'status', 'error message',
                'bugzilla number', 'log file', 'comment'
            ]]
            result_df.to_excel(
                writer,
                sheet_name='Test Results',
                startrow=1,
                index=False,
                header=False)

            # Write Log Information to workbook
            logresult.logAnalyze(var_sysosid)
            logret = session.query(SQLClass.logresult).all()
            if logret:
                key, data = toexcel.query_log(logret)
                df = pd.DataFrame(data, columns=key)
                df = df[[
                    'no', 'information', 'error type', 'error source',
                    'log file', 'bugzilla number'
                ]]
                df.to_excel(
                    writer,
                    sheet_name='Log Information',
                    startrow=1,
                    index=False,
                    header=False)
            else:
                message = "log information not found in database"
                autotestlog.logger.error(message)
            #Workbook Format
            workbook = writer.book
            #header format
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
            #format Test Report worksheet
            sc_worksheet = writer.sheets['Test Report']
            sc_worksheet.set_column('A:A', 20)
            sc_worksheet.set_column('B:B', 30)
            sc_worksheet.set_column('D:D', 30)
            sc_worksheet.set_column('E:E', 50)
            for col_num, value in enumerate(config_df.columns.values):
                sc_worksheet.write(0, col_num + 3, value, header_format)
            for col_num, value in enumerate(tester_df.columns.values):
                sc_worksheet.write(0, col_num, value, header_format)
            for col_num, value in enumerate(tc_df.columns.values):
                sc_worksheet.write(6, col_num, value, header_format)
            for row, value in enumerate(config_df.values):
                for col in range(2):
                    sc_worksheet.write(row + 1, col + 3, value[col],
                                       cell_format)
            for row, value in enumerate(tester_df.values):
                for col in range(2):
                    sc_worksheet.write(row + 1, col, value[col], cell_format)
            for row, value in enumerate(tc_df.values):
                for col in range(2):
                    sc_worksheet.write(row + 7, col, value[col], cell_format)
            # format Test Results worksheet
            tr_worksheet = writer.sheets['Test Results']
            tr_worksheet.set_column('A:A', 10)
            tr_worksheet.set_column('B:B', 20)
            tr_worksheet.set_column('C:C', 10)
            tr_worksheet.set_column('D:D', 70)
            tr_worksheet.set_column('E:E', 20)
            tr_worksheet.set_column('F:F', 30)
            tr_worksheet.set_column('G:G', 20)
            for col_num, value in enumerate(result_df.columns.values):
                tr_worksheet.write(0, col_num, value, header_format)
            # format Log Information worksheet
            li_worksheet = writer.sheets['Log Information']
            li_worksheet.set_column('A:A', 10)
            li_worksheet.set_column('B:B', 100)
            li_worksheet.set_column('C:C', 20)
            li_worksheet.set_column('D:D', 20)
            li_worksheet.set_column('E:E', 40)
            li_worksheet.set_column('F:F', 20)
            for col_num, value in enumerate(df.columns.values):
                li_worksheet.write(0, col_num, value, header_format)
            for row, value in enumerate(df.values):
                for col in range(6):
                    li_worksheet.write(row + 1, col, value[col], cell_format)
            writer.save()
            workbook.close()
            print("Create file %s") % filename
        except Exception as e:
            session.rollback()
            print "Error change the report flag in systemos table"
            autotestlog.logger.error(e.message)
    else:
        message = "test report list not found in database"
        autotestlog.logger.error(message)


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
                print "verbose is %s, the system_osid is %d" % (str(verbose),
                                                                var_sysosid)
    else:
        usage()
        sys.exit(2)


#Report()
def testReport(ret):
    if ret:
        #connect to the database
        engine = model.connectDB("Linux")
        print "Create database session..."
        DBSession = sessionmaker(bind=engine)
        session = DBSession()
        print "Done."
        #Clear the report table
        try:
            session.query(SQLClass.report).delete()
            session.commit()
            print "remove report"
        except Exception as e:
            session.rollback()
            autotestlog.logger.error(e.message)
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
    testReport(ret)
