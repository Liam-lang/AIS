#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Mar 5, 2018
webapp.py: website provider
@author: Neo
'''
import sys, os, md5, time, re, threading
import logging
import pandas as pd
import numpy as np
from flask import Flask, flash, redirect, render_template, request, session, json, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import *
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime

#for ais.labs.lenovo.com
sys.path.append("/srv/www/htdocs/DataServer")
#for https://10.245.100.27/
sys.path.append("/opt/lenovo/AIS/www/DataServer")

from sqlserver import SQLClass
from analyze.report import getresult
from common import model

#directory for saving config file such as Feature_IP_taskID.cfg
TASK_CONFIG_FOLDER = '/etc/opt/lenovo/AIS/conf/task'
#directory for saving OS unattended config file
OS_CONFIG_FOLDER = '/etc/opt/lenovo/AIS/conf/OSUnattendedFile'
#directory for saving chack base such as PCIID
PCIID_CKBASE_FOLDER ='/var/opt/lenovo/AIS/checkbase/PCIID'
#directory for saving chack base such as ISO
ISO_CKBASE_FOLDER ='/var/opt/lenovo/AIS/checkbasse/ISO'
#directory for saving script such as XXX.py
SCRIPT_FOLDER = '/opt/lenovo/AIS/testcase'
#directory for saving script such as XXX.py on SUT
SCRIPT_FOLDER_SUT = '/home/scripts'
#directory for saving webapp log
WEBAPP_LOG='/var/opt/lenovo/AIS/log/webapp.log'


RSYNC_CONF='/etc/rsyncd.conf'
RSYNC_CONF_BACK='/etc/rsyncd.conf.bak1'

lock = threading.Lock()


#app initialization
app = Flask(__name__)
app.secret_key = 't\x86\x8a+<y\x03\x0b\x0f\xafh\x14m\x06\xfeK\xd4]\x83\xd2\x08\xa0?'
app.config['TASK_CONFIG_FOLDER'] = TASK_CONFIG_FOLDER
app.config['OS_CONFIG_FOLDER'] = OS_CONFIG_FOLDER
app.config['PCIID_CKBASE_FOLDER'] = PCIID_CKBASE_FOLDER
app.config['ISO_CKBASE_FOLDER'] = ISO_CKBASE_FOLDER
app.config['SCRIPT_FOLDER'] = SCRIPT_FOLDER
app.config['SCRIPT_FOLDER_SUT'] = SCRIPT_FOLDER_SUT
app.config['WEBAPP_LOG'] = WEBAPP_LOG
app.config['RSYNC_CONF'] = RSYNC_CONF
app.config['RSYNC_CONF_BACK'] = RSYNC_CONF_BACK

TASK_STATUS_FAILED = -1
TASK_STATUS_SUCESS = 1

DBname = "Linux"
DBInstance ={'session':"",'engine':""}

DBInstance = model.createDBInstance(DBname)
db_session = DBInstance['session']

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s %(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(message)s',
                    datefmt='%Y %b %d  %H:%M:%S',
                    filename=app.config['WEBAPP_LOG'],
                    filemode='a+')


#webpage initialization
@app.route('/')
def login():
    logging.debug("login page start.")
    return render_template('login.html')


@app.route('/home')
def home():
    if session.get('logged_in'):
        logging.debug("home page start.")
        return render_template('home.html')
    else:
        logging.debug("Unauthorized access when home page start")
        return error('Unauthorized access')


@app.route('/log')
def log():
    if session.get('logged_in') and session.get('permit') == '0':
        logging.debug("log page start.")
        return render_template('log.html', username=session.get('logged_in'), userpermit=session.get('permit'))
    else:
        logging.debug("Unauthorized access when log page start")
        return error('Unauthorized access')


@app.route('/device')
def device():
    if session.get('logged_in') and session.get('permit') == '0':
        logging.debug("device page start.")
        return render_template(
            'device.html', username=session.get('logged_in'), userpermit=session.get('permit'))
    else:
        logging.debug("Unauthorized access when device page start.")
        return error('Unauthorized access')


@app.route('/report')
def report():
    if session.get('logged_in'):
        logging.debug("report page start.")
        return render_template(
            'report.html', username=session.get('logged_in'), userpermit=session.get('permit'))
    else:
        logging.debug("Unauthorized access when report page start.")
        return error('Unauthorized access')


# @app.route('/onlydevice')
# def onlydevice():
#     if session.get('logged_in') and session.get('permit') == '1':
#         return render_template(
#             'onlydevice.html', username=session.get('logged_in'), userpermit=session.get('permit'))
#     else:
#         return error('Unauthorized access for OnlyDevice Page')


@app.route('/controlServer')
def controlServer():
    if session.get('logged_in') and session.get('permit') == '0':
        logging.debug("controlServer page start.")
        return render_template(
            'controlServer.html', username=session.get('logged_in'), userpermit=session.get('permit'))
    else:
        logging.debug("Unauthorized access when controlServer page start.")
        return error('Unauthorized access')

@app.route('/OSImage')
def OSImage():
    if session.get('logged_in') and session.get('permit') == '0':
        logging.debug("OSImage page start.")
        return render_template(
            'OSImage.html', username=session.get('logged_in'), userpermit=session.get('permit'))
    else:
        logging.debug("Unauthorized access when OSImage page start.")
        return error('Unauthorized access')

@app.route('/testcase')
def TestCase():
    if session.get('logged_in') and session.get('permit') == '0':
        logging.debug("testcase page start.")
        return render_template(
            'testcase.html', username=session.get('logged_in'), userpermit=session.get('permit'))
    else:
        logging.debug("Unauthorized access when testcase page start.")
        return error('Unauthorized access')

@app.route('/task')
def task():
    if session.get('logged_in'):
        logging.debug("task page start.")
        return render_template(
            'task.html', username=session.get('logged_in'), userpermit=session.get('permit'))
    else:
        logging.debug("Unauthorized access when task page start.")
        return error('Unauthorized access')

@app.route('/error')
def error(info):
    return render_template('error.html', error=info)


@app.route("/logout")
def logout():
    model.disconnectDB(DBInstance)
    session.pop('logged_in', None)
    session.pop('permit', None)
    return login()


#end webpage initialization


#user sign in interface
#function: do_admin_login
@app.route('/login', methods=['POST'])
def do_admin_login():
    POST_USERNAME = str(request.form['username'])
    POST_PASSWORD = str(request.form['password'])
    mdobj = md5.new()
    mdobj.update(POST_PASSWORD)
    mdobj = mdobj.hexdigest()

    query = db_session.query(SQLClass.user).filter(
        SQLClass.user.username.in_([POST_USERNAME]))
    result = query.first()
    if result:
        if mdobj != result.password or request.form['username'] != result.username:
            flash(message='Wrong Credentials!', category='danger')
            return login()
        else:
            session['logged_in'] = result.firstname + result.lastname
            ret_permit = db_session.query(SQLClass.role).filter(
                SQLClass.role.userid == result.userid).first()
            if (ret_permit):
                session['permit'] = ret_permit.permission.value
                history = SQLClass.login_history(
                    userid=result.userid, history=datetime.utcnow())
                try:
                    db_session.add(history)
                    db_session.commit()
                except Exception as e:
                    db_session.rollback()
                    flash(
                        message="Record login history failed!" + str(e),
                        category='danger')
                    return login()
                return home()
            else:
                flash(
                    message="Check your permission failed! \
                            Please contact with Administrator.",
                    category='danger')
                return login()
    else:
        flash(
            message="User doesn't exist! Please confirm your user name.",
            category='danger')
        return login()


#end do_admin_login()


#user sign up interface
#function: register
@app.route('/register', methods=['POST'])
def register():
    POST_FNAME = str(request.form['fname'])
    POST_LNAME = str(request.form['lname'])
    POST_USERNAME = str(request.form['username'])
    POST_PASSWORD = str(request.form['password'])
    mdobj = md5.new()
    mdobj.update(POST_PASSWORD)
    mdobj = mdobj.hexdigest()
    new_user = SQLClass.user(
        firstname=POST_FNAME,
        lastname=POST_LNAME,
        username=POST_USERNAME,
        password=mdobj)
    try:
        db_session.add(new_user)
        db_session.flush()
        user_permit = SQLClass.role(userid=new_user.userid)
        try:
            db_session.add(user_permit)
            db_session.commit()
            flash(message="Register Success.", category='success')
            return login()
        except Exception as e:
            db_session.rollback()
            if e.message.find("Duplicate entry") != -1:
                flash(
                    message="Already registered user with permission.",
                    category='info')
                return login()
    except Exception as e:
        db_session.rollback()
        if e.message.find("Duplicate entry") != -1:
            flash(message="Already registered user", category='info')
            return login()
    return error("Register Failed!")


#end register


#Start log information handle section
#show new html page (addlog.html) bind with  add log interface
#function: showAddLog
# @app.route('/showAddLog')
# def showAddLog():
#     if session.get('logged_in') and session.get('permit') == '0':
#         return render_template('addlog.html')
#     else:
#         return error('Unauthorized Access')

#end showAddLog


#get log information by logid called by log.html operation - edit log
#function: getLogById
@app.route('/getLogById', methods=['POST'])
def getLogById():
    try:
        if session.get('logged_in') and session.get('permit') == '0':
            POST_ID = request.form['logid']
            query = db_session.query(
                SQLClass.log).filter(SQLClass.log.logid == POST_ID).first()
            if query:
                record = []
                record.append({
                    'Id': query.logid,
                    'Information': query.information,
                    'Comment': query.comment,
                    'Bznumber': query.bznumber,
                    'Status': query.status.value
                })
                return json.dumps(record)
            else:
                flash(
                    message="Record not found in database.",
                    category='warning')
                return log()
        else:
            return error('Unauthorized Access')
    except Exception as e:
        return error(str(e))


#end getLogById


#get platform/OS information by logid called by log.html operation - tag
#function: getTagById
@app.route('/getTagById', methods=['POST'])
def getTagById():
    try:
        if session.get('logged_in') and session.get('permit') == '0':
            POST_ID = request.form['tagLogId']
            log = db_session.query(
                SQLClass.log).filter(SQLClass.log.logid == POST_ID).first()
            if log:
                log_sys_os = db_session.query(SQLClass.log_system_os).filter(
                    SQLClass.log_system_os.logid == log.logid).all()
                if log_sys_os:
                    records = []
                    for item in log_sys_os:
                        sys_os = db_session.query(SQLClass.system_os).filter(
                            SQLClass.system_os.system_osid ==
                            item.systemosid).first()
                        system_obj = db_session.query(
                            SQLClass.system).filter(SQLClass.system.systemid ==
                                                    sys_os.systemid).first()
                        OS_obj = db_session.query(SQLClass.os).filter(
                            SQLClass.os.osid == sys_os.osid).first()
                        if system_obj and OS_obj:
                            record_dict = {
                                'Platform':
                                system_obj.series.value + ' ' +
                                system_obj.model,
                                'OS':
                                OS_obj.name + OS_obj.version,
                                'Phase':
                                OS_obj.phase,
                            }
                            if record_dict not in records:
                                records.append(record_dict)
                        else:
                            flash(
                                message="System/OS not found in database.",
                                category='warning')
                            return log()
                    return json.dumps(records)
                else:
                    flash(
                        message="System/OS not found in database.",
                        category='warning')
                    return log()
            else:
                flash(
                    message="System/OS not found in database.",
                    category='warning')
                return log()
        else:
            return error('Unauthorized Access')
    except Exception as e:
        return error(str(e))


#end getTagById


#log.html operation - update log
#function: updateLog
@app.route('/updateLog', methods=['POST'])
def updateLog():
    try:
        if session.get('logged_in') and session.get('permit') == '0':
            _comment = request.form['comment']
            _status = request.form['stat']
            _bznumber = request.form['bznumber']
            _log_id = request.form['logid']
            query = db_session.query(
                SQLClass.log).filter(SQLClass.log.logid == _log_id).first()
            query.comment = _comment
            query.status = _status
            query.bznumber = _bznumber
            try:
                db_session.commit()
                return json.dumps({'status': 'OK'})
            except Exception as e:
                db_session.rollback()
                return json.dumps({'status': 'ERROR'})
        else:
            return error('Unauthorized Access')
    except Exception as e:
        return json.dumps({'status': str(e)})


#end updateLog


#log.html operation - delete log
#function: deleteLog
@app.route('/deleteLog', methods=['POST'])
def deleteLog():
    try:
        if session.get('logged_in') and session.get('permit') == '0':
            POST_ID = request.form['logids'].split(',')
            for ID in POST_ID:
                query = db_session.query(
                    SQLClass.log).filter(SQLClass.log.logid == ID).first()
                try:
                    db_session.delete(query)
                    db_session.commit()
                except Exception as e:
                    db_session.rollback()
                    return json.dumps({'status': 'An Error occurred'})
            return json.dumps({'status': 'OK', 'Ids': POST_ID})
        else:
            return error('Unauthorized Access')
    except Exception as e:
        return json.dumps({'status': str(e)})


#end deleteLog


#get all the log information from database
#and show them on the html table
#function: getLog
@app.route('/getLog', methods=['POST', 'GET'])
def getLog():
    if request.method == 'POST':
        print "post"
    if request.method == 'GET':
        try:
            limit = int(request.values.get('limit'))
            offset = int(request.values.get('offset'))
            search = request.values.get('search')
            sort = request.values.get('sort')
            order = request.values.get('order')
            if session.get('logged_in') and session.get('permit') == '0':
                if search is not None and search != '':
                    filter_sql = text(
                        "information like :pattern or source like :pattern or comment like :pattern or status like :pattern"
                    ).bindparams(pattern='%' + search + '%')
                else:
                    filter_sql = text("logid is not null")
                if sort is not None:
                    if sort == "Id":
                        sort_sql = text("logid " + order)
                    elif sort == "Source":
                        sort_sql = text("source " + order)
                    elif sort == "Status":
                        sort_sql = text("status " + order)
                else:
                    sort_sql = text("logid")
                count = db_session.query(
                    SQLClass.log).filter(filter_sql).count()
                query = db_session.query(SQLClass.log).order_by(
                    sort_sql).filter(filter_sql).limit(limit).offset(offset)
                records_dict = []
                for item in query.all():
                    record_dict = {
                        'Id': item.logid,
                        'Comment': item.comment,
                        'Information': item.information,
                        'Source': item.source.value,
                        'Status': item.status.value,
                        'Bznumber': item.bznumber
                    }
                    records_dict.append(record_dict)
                return jsonify({'total': count, 'rows': records_dict})
            else:
                return error('Unauthorized Access')
        except Exception as e:
            return error(str(e))


#end getLog


# Deprecated
# add new log interface on addlog.html
# function: addLog
@app.route('/addLog', methods=['POST'])
def addLog():
    try:
        if session.get('logged_in') and session.get('permit') == '0':
            _information = request.form['inputInfo']
            _error_type = request.form['inputError_Type']
            _source = request.form['inputSrc']
            _status = request.form['inputStat']
            _comment = request.form['inputComment']
            _bznumber = request.form['inputBZ']
            mdobj = md5.new()
            mdobj.update(_information)
            mdobj = mdobj.hexdigest()
            new_record = SQLClass.log(
                information=_information,
                error_type=_error_type,
                source=_source,
                comment=_comment,
                status=_status,
                bznumber=_bznumber,
                md5=mdobj)
            try:
                db_session.add(new_record)
                db_session.commit()
                return log()
            except Exception as e:
                db_session.rollback()
                if e.message.find("Duplicate entry") != -1:
                    flash(
                        message="Duplicated records found in database.",
                        category='warning')
                return log()
        else:
            return error('Unauthorized Access')
    except Exception as e:
        return error(str(e))


#end addLog
#end log information handle section


#Start device (pciid) information handle section
#show new html page (device.html) to add new device pciid information
#function: showAddDevice
# @app.route('/showAddDevice')
# def showAddDevice():
#     if session.get('logged_in'):
#         return render_template('adddevice.html')
#     else:
#         return error('Unauthorized Access')

#end showAddDevice


#get device information by deviceid (pciidid) called by device operation -
#edit and delete
#function: getDeviceById
@app.route('/getDeviceById', methods=['POST'])
def getDeviceById():
    logging.debug("getDeviceById start.")
    try:
        if session.get('logged_in'):
            POST_ID = request.form['pciidid']
            logging.info("POST_ID is %d ." %(POST_ID))
            query = db_session.query(SQLClass.pciid).filter(
                SQLClass.pciid.pciidid == POST_ID).first()
            logging.info("Get data from pciid_table succeed.")
            if query:
                record = []
                record.append({
                    'Id': query.pciidid,
                    'Vendor': query.vendor,
                    'Description': query.description,
                    'Vendorid': query.vendorid,
                    'Deviceid': query.deviceid,
                    'Subvendorid': query.subvendorid,
                    'Subdeviceid': query.subdeviceid,
                    'Project': query.project,
                    'Status': query.status.value
                })
                logging.debug("getDeviceById end when dump json.")
                return json.dumps(record)
            else:
                flash(
                    message="Device not found in database.",
                    category='warning')
                logging.debug("getDeviceById end when device not found.")
                return device()
        else:
            logging.error("getDeviceById end when unauthorized Access.")
            return error('Unauthorized Access')
    except Exception as e:
        logging.error("getDeviceById end when error occurred : %s" %(str(e)))
        return error(str(e))

#end getDeviceById


#device.html operation - edit one device information
#function: updateDevice
@app.route('/updateDevice', methods=['POST'])
def updateDevice():
    try:
        if session.get('logged_in'):
            _project = request.form['inputPro']
            _vid = request.form['vendorid']
            _did = request.form['deviceid']
            _svid = request.form['subvendorid']
            _sdid = request.form['subdeviceid']
            _status = request.form['inputStat']
            _pci_id = request.form['pciidid']
            query = db_session.query(SQLClass.pciid).filter(
                SQLClass.pciid.pciidid == _pci_id).first()
            query.project = _project
            query.vendorid = _vid
            query.deviceid = _did
            query.subvendorid = _svid
            query.subdeviceid = _sdid
            query.status = _status
            try:
                db_session.commit()
                return json.dumps({'status': 'OK'})
            except Exception as e:
                db_session.rollback()
                return json.dumps({'status': 'ERROR'})
        else:
            return error('Unauthorized Access')
    except Exception as e:
        return json.dumps({'status': str(e)})

#end updateDevice


#device.html oeration - delete one device information
#function: deleteDevice
@app.route('/deleteDevice', methods=['POST'])
def deleteDevice():
    try:
        if session.get('logged_in'):
            POST_ID = request.form['pciidids'].split(',')
            for ID in POST_ID:
                query = db_session.query(SQLClass.pciid).filter(
                    SQLClass.pciid.pciidid == ID).first()
                try:
                    db_session.delete(query)
                    db_session.commit()
                except Exception as e:
                    db_session.rollback()
                    return json.dumps({'status': 'An Error occurred'})
            return json.dumps({'status': 'OK', 'Ids': POST_ID})
        else:
            return error('Unauthorized Access')
    except Exception as e:
        return json.dumps({'status': str(e)})

#end deleteDevice


#get all the device information from database
#and show them on the html table
#fucntion: getDevice
@app.route('/getDevice', methods=['GET'])
def getDevice():
    logging.debug("getDevice start.")
    try:
        if session.get('logged_in'):
            query = db_session.query(SQLClass.pciid).order_by(
                SQLClass.pciid.pciidid)
            logging.info("Get data from pciid_table succeed.")
            records_dict = []
            for item in query.all():
                record_dict = {
                    'Id': item.pciidid,
                    'Vendor': item.vendor,
                    'Description': item.description,
                    'Vendorid': item.vendorid,
                    'Deviceid': item.deviceid,
                    'Subvendorid': item.subvendorid,
                    'Subdeviceid': item.subdeviceid,
                    'Driver': item.drivername,
                    'Version': item.driverversion,
                    'Project': item.project,
                    'Status': item.status.value
                }
                records_dict.append(record_dict)
            logging.debug("getDevice end when dump json.")
            return json.dumps(records_dict)
        else:
            logging.error("getDevice end when unauthorized Access.")
            return error('Unauthorized Access')
    except Exception as e:
        logging.error("getDevice end when error occurred : %s" %(str(e)))
        return error(str(e))


#end getDevice


#add new device information on adddevice.html
#function: addDevice
@app.route('/addDevice', methods=['POST'])
def addDevice():
    try:
        if session.get('logged_in'):
            _vendor = request.form['inputVendor']
            _project = request.form['inputPro']
            _description = request.form['inputDes']
            _vid = request.form['vendorid']
            _did = request.form['deviceid']
            _svid = request.form['subvendorid']
            _sdid = request.form['subdeviceid']
            _status = request.form['inputStat']
            new_record = SQLClass.pciid(
                vendor=_vendor,
                description=_description,
                vendorid=_vid,
                deviceid=_did,
                subvendorid=_svid,
                subdeviceid=_sdid,
                project=_project,
                status=_status)
            try:
                db_session.add(new_record)
                db_session.commit()
                return device()
            except Exception as e:
                db_session.rollback()
                if e.message.find("Duplicate entry") != -1:
                    flash(
                        message="Duplicated device found in database.",
                        category='warning')
                return device()
        else:
            return error('Unauthorized Access')
    except Exception as e:
        return error(str(e))


#end addDevice

#upload PCIID on device.html
#function: uploadPCIID
@app.route('/uploadPCIID', methods=['POST'])
def uploadPCIID():
    logging.debug('uploadPCIID() start')
    if session.get('logged_in'):
            try:
                if 'uploadPCIID' not in request.files:
                    logging.error("uploadPCIID() end when no file part")
                    return json.dumps({'error': 'No file part'})
                file = request.files['uploadPCIID']
                if file.filename == '':
                    logging.error("uploadPCIID() end when no selected file")
                    return json.dumps({'error': 'No selected file'})
                if file and allowed_file(file.filename,['xlsx', 'xls','txt']):
                    filename = secure_filename(file.filename)
                    if filename[-3:] == "txt":
                        flag_1 = filename.partition('Installer-')[2]
                        if filename.find('update') == -1:
                            filesave_path = model.driverDir +  'VMware/' + flag_1[:flag_1.find('-')] + '/'
                        else:
                            filesave_path = model.driverDir +  'VMware/' + flag_1[:flag_1.find('.update')] + '/'
                        if os.path.exists(filesave_path)==False:
                            os.mkdir(filesave_path)
                        logging.info('driver name is %s' % (filename))
                        file.save(os.path.join(filesave_path,filename))
                    else:
                        logging.info('PCIID name is %s' % (filename))
                        file.save(os.path.join(app.config['PCIID_CKBASE_FOLDER'], filename))
                logging.debug('uploadPCIID() end when dump json.')
                return json.dumps({'status': 'OK'})
            except Exception as e:
                logging.error('uploadPCIID() end when error occurred : %s' %(str(e)))
                return json.dumps({'error': str(e)})
    else:
            logging.error('uploadPCIID() end when unauthorized Access')
            return json.dumps({'error': 'Unauthorized Access'})
#end uploadPCIID

#insert record to db from exel after upload PCIID on device.html
#function : getDeviceAfterUpload
# @app.route('/getDeviceAfterUpload', methods=['GET'])
# def getDeviceAfterUpload():
#     logging.debug("getDeviceAfterUpload() start.")
#     # delete all the data in pciid table
#     excelExist = False
#     try:
#         db_session.query(SQLClass.pciid).delete(synchronize_session=False)
#         db_session.commit()
#         logging.info("delete pciid_table succeed.")
#     except Exception as e:
#         db_session.rollback()
#         logging.error("an error occurred when cleare pciid_table : " + str(e))
#
#     # insert the pciid info to the pciid table
#     files = os.listdir(model.pciidDir)
#     ## get the pciid excel file downloaded from IO website
#     if files:
#         for f in files:
#             if f.find('.xlsx') >= 0:
#                 excelExist = True
#                 filename = os.path.join(model.pciidDir, f)
#                 pf = pd.read_excel(io=filename)
#                 logging.info("len(pf)=%d" % (len(pf)))
#                 for i in range(0, len(pf)):
#                     vd = pf.ix[i, "vendor"]
#                     desc = pf.ix[i, "String name"]
#                     VD_ID = pf.ix[i, "Device PCI ID(VendorID:DeviceID)"]
#                     posvd = VD_ID.find(":")
#                     vid = VD_ID[:posvd]
#                     did = VD_ID[posvd + 1:]
#                     SUBVD_ID = pf.ix[i, "SubvendorID:SubdeviceID(SubdeviceID may not unique)"]
#                     # logging.debug("SUBVD_ID is " + SUBVD_ID)
#                     # logging.debug("the type of SUBVD is " + type(SUBVD_ID))
#                     if isinstance(SUBVD_ID, float) and np.isnan(SUBVD_ID):
#                         subvid = ""
#                         subdid = ""
#                     else:
#                         possubvd = SUBVD_ID.find(":")
#                         subvid = SUBVD_ID[:possubvd]
#                         subdid = SUBVD_ID[possubvd + 1:]
#                     pro = pf.ix[i, "Project(Initial Introduced)"]
#                     if np.isnan(pro):
#                         pro = ""
#                     pciidItem = SQLClass.pciid(
#                         #    device=dv,
#                         vendor=vd,
#                         description=desc,
#                         vendorid=vid,
#                         deviceid=did,
#                         subvendorid=subvid,
#                         subdeviceid=subdid,
#                         project=pro,
#                         status="valid")
#                     try:
#                         db_session.add(pciidItem)
#                         db_session.flush()
#                         db_session.commit()
#                     except Exception as e:
#                         db_session.rollback()
#                         logging.error("an error occurred when add record to pciid_table : " + str(e))
#             os.remove(filename)
#             logging.info("delete pciid file %s" % (f))
#         if excelExist == True:
#             return getDevice()
#         else :
#             flash(
#                 message="There is no excel file in the %s directory" %(model.pciidDir),
#                 category='danger')
#             return json.dumps([])
#     else:
#         flash(
#             message="There is no excel file in the %s directory" % (model.pciidDir),
#             category='danger')
#         logging.error("There is no excel file in the %s directory" %(model.pciidDir))
#         return json.dumps([])

# end uploadPCIID
# end device information handle section
#report information handle section
#function: getReport. Get all the available reports
@app.route('/getReport', methods=['GET'])
def getReport():
    logging.debug("getReport() start.")
    try:
        if session.get('logged_in'):
            db_session.commit()
            RHEL_OS_groups = db_session.query(
                SQLClass.os.version,
                func.group_concat(SQLClass.os.osid.distinct())).join(
                    SQLClass.system_os, isouter=True).filter(
                        and_(
                            or_(SQLClass.os.driverflag ==
                                model.stsEnum.valid.value,
                                SQLClass.system_os.reportflag ==
                                model.stsEnum.valid.value), SQLClass.os.name ==
                            "Red Hat Enterprise Linux Server")).group_by(
                                SQLClass.os.version).all()
            logging.info("Get RHEL_OS_groups succeed.")
            rhel_records_dict = {}
            if RHEL_OS_groups:
                for group in RHEL_OS_groups:
                    group_head = group
                    osversion, ids = group
                    ids = str(ids).split(',')
                    oses_dict = []
                    for osid in ids:
                        OS_obj = db_session.query(SQLClass.os).filter(
                            SQLClass.os.osid == osid).first()
                        if OS_obj:
                            osdict = {
                                'OSId': OS_obj.osid,
                                'OS': OS_obj.name,
                                'Version': OS_obj.version,
                                'Phase': OS_obj.phase,
                            }
                            oses_dict.append(osdict)
                    rhel_records_dict[osversion] = oses_dict
            else:
                logging.info("RHEL_OS_groups is NULL.")
            logging.info(rhel_records_dict)

            SLES_OS_groups = db_session.query(
                SQLClass.os.version,
                func.group_concat(SQLClass.os.osid.distinct())).join(
                    SQLClass.system_os, isouter=True).filter(
                        and_(
                            or_(SQLClass.os.driverflag ==
                                model.stsEnum.valid.value,
                                SQLClass.system_os.reportflag ==
                                model.stsEnum.valid.value), SQLClass.os.name ==
                            "SUSE Enterprise Linux Server")).group_by(
                                SQLClass.os.version).all()
            logging.info("Get SLES_OS_groups succeed.")
            sles_records_dict = {}
            if SLES_OS_groups:
                for group in SLES_OS_groups:
                    group_head = group
                    osversion, ids = group
                    ids = str(ids).split(',')
                    oses_dict = []
                    for osid in ids:
                        OS_obj = db_session.query(SQLClass.os).filter(
                            SQLClass.os.osid == osid).first()
                        if OS_obj:
                            osdict = {
                                'OSId': OS_obj.osid,
                                'OS': OS_obj.name,
                                'Version': OS_obj.version,
                                'Phase': OS_obj.phase,
                            }
                            oses_dict.append(osdict)
                    sles_records_dict[osversion] = oses_dict
            else:
                logging.info("SLES_OS_groups is NULL.")
            logging.info(sles_records_dict)

            VMware_OS_groups = db_session.query(
                SQLClass.os.version,
                func.group_concat(SQLClass.os.osid.distinct())).join(
                    SQLClass.system_os, isouter=True).filter(
                        and_(
                            or_(SQLClass.os.driverflag ==
                                model.stsEnum.valid.value,
                                SQLClass.system_os.reportflag ==
                                model.stsEnum.valid.value), SQLClass.os.name ==
                            "VMware")).group_by(
                                SQLClass.os.version).all()
            logging.info("Get VMware_OS_groups succeed.")
            vmware_records_dict = {}
            if VMware_OS_groups:
                for group in VMware_OS_groups:
                    group_head = group
                    osversion, ids = group
                    ids = str(ids).split(',')
                    oses_dict = []
                    for osid in ids:
                        OS_obj = db_session.query(SQLClass.os).filter(
                            SQLClass.os.osid == osid).first()
                        if OS_obj:
                            osdict = {
                                'OSId': OS_obj.osid,
                                'OS': OS_obj.name,
                                'Version': OS_obj.version,
                                'Phase': OS_obj.phase,
                            }
                            oses_dict.append(osdict)
                    vmware_records_dict[osversion] = oses_dict
            else:
                logging.info("VMware_OS_groups is NULL.")
            logging.info(vmware_records_dict)
            logging.debug("getReport() end when dump json.")
            return json.dumps({
                "RHEL": rhel_records_dict,
                "SLES": sles_records_dict,
                "VMware":vmware_records_dict
            })
        else:
            logging.error("getReport() end when unauthorized Access.")
            return error('Unauthorized Access')
    except Exception as e:
        logging.error("getReport() end when error occurred : %s" %(str(e)))
        return error(str(e))


#end getReport
#function: getReportByConfig
@app.route('/getReportByConfig', methods=['POST'])
def getReportByConfig():
    logging.debug("getReportByConfig() start.")
    file_type = ('pci', 'report')
    try:
        if session.get('logged_in'):
            POST_ID = request.form['osid']
            records_dict = []
            os_obj = db_session.query(
                SQLClass.os).filter(SQLClass.os.osid == POST_ID).first()
            logging.info("Get data from os_table succeed.")
            if os_obj.driverflag.value == model.stsEnum.valid.value:
                image_name=os_obj.imgname[:-4] + "_" + "(\d+)" + ".xlsx"
                logging.debug('iso is %s' % image_name)
                for dirpath, dirnames, filenames in os.walk(model.driverDir):
                    for file in filenames:
                        filter_task = re.compile(image_name)
                        filter_id=filter_task.findall(file)
                        for taskid in filter_id:
                            record_dict = {
                                'OSId': os_obj.osid,
                                'Platform': '',
                                'Date': '',
                                'Type': file_type[0],
                                'TaskId':taskid,
                            }
                            records_dict.append(record_dict)

            query = db_session.query(SQLClass.system_os).filter(
                SQLClass.system_os.osid == POST_ID).all()
            logging.info("Query data from system_os succeed.")
            if query:
                for item in query:
                    sys_obj = db_session.query(SQLClass.system).filter(
                        SQLClass.system.systemid == item.systemid).first()
                    if item.reportflag.value == model.stsEnum.valid.value:
                        record_dict = {
                            'Id': item.system_osid,
                            'Platform': sys_obj.model,
                            'Date': item.creation,
                            'Type': file_type[1]
                        }
                        records_dict.append(record_dict)
            if records_dict == []:
                flash(
                    message='Records not found in database!',
                    category='danger')
                logging.debug("getReportByConfig() end when records not found in system_os.")
                return json.dumps(records_dict)
            logging.debug("getReportByConfig() end when dump json.")
            return json.dumps(records_dict)
        else:
            logging.error("getReportByConfig() end when unauthorized Access.")
            return error('Unauthorized Access')
    except Exception as e:
        logging.error("getReportByConfig() end when error occurred : %s" % (str(e)))
        return error(str(e))


#end getReportByConfig

#report.html operation - update report 
#function: updateReport
@app.route('/updateReport', methods=['POST'])
def updateReport():
    logging.debug("updateReport() start.")
    try:
        if session.get('logged_in'):
            _sysosid = request.form['sysosid']
            _engineer = request.form['engineer']
            _tester = request.form['tester']
            _bios_bmc = request.form['bios_bmc']
            _memory = request.form['memory']
            _raid = request.form['raid']
            _hba = request.form['hba']
            _hdd = request.form['hdd']
            _nic = request.form['nic']
            _gpu = request.form['gpu']
            query = db_session.query(
                SQLClass.system_os).filter(SQLClass.system_os.system_osid == _sysosid).first()
            if query:
                query.engineer = _engineer
                query.tester = _tester
                query.memory = _memory
                query.raid = _raid
                query.hba= _hba
                query.hdd= _hdd
                query.nic= _nic
                query.gpu= _gpu
                query.biosver= _bios_bmc
                try:
                    db_session.commit()
                    getresult(_sysosid, db_session)
                    return json.dumps({'status': 'OK'})
                except Exception as e:
                    db_session.rollback()
                    return json.dumps({'status': 'ERROR'})
            else:
                print "No system_os exists in database"
                return json.dumps({'status': 'ERROR'})
        else:
            return error('Unauthorized Access')
    except Exception as e:
        return json.dumps({'status': str(e)})
# end updateReport


#function: getFileById
@app.route('/getFileById', methods=['POST'])
def getFileById():
    logging.debug("getFileById() start.")
    osdict = {'Red Hat Enterprise Linux Server': 'RedHat', 'SUSE Enterprise Linux Server': 'SUSE','VMware':'VMware'}
    try:
        if session.get('logged_in'):
            records_dict = []
            TASK_ID,POST_ID, POST_TYPE = request.form['idtype'].split(',')
            logging.debug('idtype is %s %s %s ' % (TASK_ID,POST_ID,POST_TYPE))
            if POST_TYPE == "pci":
                query = db_session.query(SQLClass.os).filter(
                    SQLClass.os.osid == POST_ID).first()
                logging.info("query data from os_table succeed.")
                if query:
                    _version= query.version.find('.update')
                    if _version == -1:
                        pcidir = model.driverDir + osdict[query.name] + "/" + query.version + "/" + query.imgname[:-4] + '_' + TASK_ID
                        record_dict = {
                            'Id': POST_ID,
                            'logdir':'',
                            'pcidir':pcidir,
                            'time':''
                        }
                    else:
                        pcidir = model.driverDir + osdict[query.name] + "/" + query.version[:_version] + "/" + query.imgname[:-4] + '_' + TASK_ID
                        record_dict = {
                            'Id': POST_ID,
                            'logdir': '',
                            'pcidir': pcidir,
                            'time': ''
                        }
                    records_dict.append(record_dict)
                    logging.info("pci record_dict is :%s" %(record_dict))
                else:
                    flash(
                        message='No pci report found in database!',
                        category='danger')
                    logging.error("getFileById() end when no pci report found in database!")
                    return report()
            elif POST_TYPE == "report":
                query = db_session.query(SQLClass.system_os).filter(
                    SQLClass.system_os.system_osid == POST_ID).first()
                logging.info("query data from system_os succeed.")
                if query:
                    arr = query.logfile.split('_')
                    record_dict = {
                        'Id': query.system_osid,
                        'logdir': query.logfile,
                        'pcidir': '',
                        'time': arr[1]
                    }
                    records_dict.append(record_dict)
                    logging.info("report record_dict is :%s" % (record_dict))
                else:
                    flash(
                        message='No testing report found in database!',
                        category='danger')
                    logging.error("getFileById() end when no testing report found in database!")
                    return report()
            else:
                flash(
                    message='Strange Type information!',
                    category='danger')
                logging.error("getFileById() end when strange type information!")
                return report()
            logging.debug("getFileById() end when dump json.")
            return json.dumps(records_dict)
        else:
            logging.error("getFileById() end when unauthorized Access")
            return error('Unauthorized Access')
    except Exception as e:
        logging.error("getFileById() end when error occurred : %s" % (str(e)))
        return error(str(e))

# get all the control server information from database
# and show them on the controlServer.html table
# fucntion: getControlSevers
@app.route('/getControlServers', methods=['GET'])
def getControlServers():
    logging.debug("getControlServers() start.")
    try:
        if session.get('logged_in'):
            query = db_session.query(SQLClass.controlserver).order_by(
                    SQLClass.controlserver.controlserverid)
            logging.info("Query data from controlserver_table succeed.")
            records_dict = []
            for item in query.all():
                record_dict = {
                        'Id': item.controlserverid,
                        'Name': item.servername,
                        'PriIp': item.priIPaddress,
                        'PubIp': item.pubIPaddress,
                        'MAC': item.MACaddress,
                        'Location': item.location
                }
                records_dict.append(record_dict)
            logging.debug("getControlServers() end when dump json.")
            return json.dumps(records_dict)
        else:
            logging.error("getControlServers() end when unauthorized access.")
            return error('Unauthorized Access')
    except Exception as e:
            logging.error("getControlServers() end when error occurred : %s" % (str(e)))
            return error(str(e))
# end getControlServers

def changeRsyncConf(IPAddress, mode):
    logging.debug('changeRsyncConf() start')
    try:
        fopenORG = open(app.config['RSYNC_CONF'], 'r')
        fopenBAK = open(app.config['RSYNC_CONF_BACK'], 'a+')
        logging.debug("open file succeed.")
        for line in fopenORG.readlines() :
            #if hosts allow has more line than one ,there would be wrong.
            if line.find("hosts allow", 0, len(line)) != -1 :
                index = line.find("=", 0, len(line))
                if index != -1:
                    hostList = line[index+1:]
                    logging.debug('host list is : ' + hostList)
                    if mode == 1:
                        #add
                        if hostList.strip().strip(",") == "":
                            line = line.strip("\n").strip(",") + IPAddress + "\n"
                            fopenBAK.write(line)
                        else:
                            hostList = hostList.strip("\n").strip().strip(",") + "," + IPAddress + "\n"
                            line = line[:index+1] + " " + hostList
                            fopenBAK.write(line)
                    elif mode == 0:
                        #delete
                        hostList = hostList.strip("\n").strip().replace(","+IPAddress+",",",")
                        hostList = hostList.strip(",").replace(IPAddress,"").strip(",")
                        line = line[:index+1] + " " + hostList+"\n"
                        fopenBAK.write(line)
                    logging.info('new line is : ' + line)
                else:
                    fopenBAK.write(line)
                    logging.error("format of /etc/rsyncd.conf is wrong.")
            else :
                fopenBAK.write(line)
    except Exception as e:
        logging.error("An error occurred when write file: "+str(e))

    finally:
        if fopenORG:
            fopenORG.close()
        if fopenBAK:
            fopenBAK.close()
        logging.debug('fopenORG and fopenBAK closed')

    try:
        os.rename(app.config['RSYNC_CONF_BACK'],app.config['RSYNC_CONF'])
    except Exception as e:
        logging.error("An error occurred when rename: " + str(e))

    logging.debug('changeRsyncConf() end')
    return

#add new control server information on controlServer.html
#function: addControlServer
@app.route('/addControlSever', methods=['POST'])
def addControlSever():
    logging.debug("addControlSever() start.")
    try:
        if session.get('logged_in'):
            _serverName = request.form['Name']
            _pubIpAddress = request.form['PubIP']
            _priIpAddress = request.form['PriIP']
            _MACAddress = request.form['MAC']
            _Location = request.form['Location']
            new_record = SQLClass.controlserver(
                servername=_serverName,
                pubIPaddress=_pubIpAddress,
                priIPaddress=_priIpAddress,
                MACaddress=_MACAddress,
                location=_Location
            )
            try:
                db_session.add(new_record)
                db_session.commit()
                changeRsyncConf(_pubIpAddress, 1)
                logging.debug("addControlSever() end when dump json.")
                return json.dumps({'status': 'OK'})
            except Exception as e:
                db_session.rollback()
                if e.message.find("Duplicate entry") != -1:
                    flash(
                        message="Duplicated device found in database.",
                        category='warning')
                logging.error("addControlSever() end when duplicated device found in database.")
                return controlServer()
        else:
            logging.error("addControlSever() end when unauthorized access")
            return error('Unauthorized Access')
    except Exception as e:
        logging.error("addControlSever() end when error occurred : " + str(e))
        return error(str(e))
#end addControlSever

#delete control server information on controlServer.html
#function: deleteControlServers
@app.route('/deleteControlServers', methods=['POST'])
def deleteControlServers():
    logging.debug("deleteControlServers() start.")
    try:
        if session.get('logged_in'):
            POST_ID = request.form['CSIds'].split(',')
            for ID in POST_ID:
                query = db_session.query(SQLClass.controlserver).filter(
                    SQLClass.controlserver.controlserverid == ID).first()
                logging.info("Query data from controlserver_table succeed.")
                _pubIpAddress = query.pubIPaddress
                try:
                    db_session.delete(query)
                    db_session.commit()
                except Exception as e:
                    db_session.rollback()
                    logging.error("deleteControlServers() end when error occurred : " + str(e))
                    return json.dumps({'status': 'An Error occurred'})
            changeRsyncConf(_pubIpAddress, 0)
            logging.debug("deleteControlServers() end when dump json.")
            return json.dumps({'status': 'OK', 'Ids': POST_ID})
        else:
            logging.error("deleteControlServers() end when unauthorized access")
            return error('Unauthorized Access')
    except Exception as e:
        logging.error("deleteControlServers() end when error occurred : " + str(e))
        return json.dumps({'status': str(e)})
#end deleteControlServers

#end control Server information handle section

# get all the ISO Image information from database
# and show them on the OSImage.html table
# fucntion: getOSImages
@app.route('/getOSImages', methods=['GET'])
def getOSImages():
    logging.debug("getOSImages start.")
    try:
        if session.get('logged_in'):
            db_session.commit()
            query = db_session.query(SQLClass.os).order_by(
                    SQLClass.os.osid)
            logging.info("Query data from os_table succeed.")
            records_dict = []
            for item in query.all():
                record_dict = {
                        'Id': item.osid,
                        'Vender': item.name,
                        'Version': item.version,
                        'Imgname': item.imgname,
                        'Phase': item.phase,
                        'MD5': item.md5
                }
                records_dict.append(record_dict)
            logging.debug("getOSImages end when dump json.")
            return json.dumps(records_dict)
        else:
            logging.error("getOSImages end when unauthorized access.")
            return error('Unauthorized Access')
    except Exception as e:
            logging.error("getOSImages end when error occurred : %s" %(str(e)))
            return error(str(e))
# end getOSImages

#add new ISO information on OSImage.html
#function: addOSImage
@app.route('/addOSImage', methods=['POST'])
def addOSImage():
    logging.debug("addOSImage() start.")
    try:
        if session.get('logged_in'):
            _vender = request.form['Vender']
            _version = request.form['Version']
            _phase = request.form['Phase']
            _isoname = request.form['ISO']
            _md5code = request.form['MD5']
            _platform = model.plmEnum.x86_64

            new_record = SQLClass.os(
                name=_vender,
                version=_version,
                phase=_phase,
                imgname=_isoname,
                md5=_md5code,
                platform=_platform
            )
            try:
                db_session.add(new_record)
                db_session.commit()
                logging.debug("addOSImage() end when dump json.")
                return json.dumps({'status': 'OK'})
            except Exception as e:
                db_session.rollback()
                if e.message.find("Duplicate entry") != -1:
                    flash(
                        message="Duplicated device found in database.",
                        category='warning')
                logging.error("addOSImage() end when error occurred : %s" %(str(e)))
                return OSImage()
        else:
            logging.error("addOSImage() end when unauthorized access")
            return error('Unauthorized Access')
    except Exception as e:
        logging.error("addOSImage() end when error occurred : %s" % (str(e)))
        return error(str(e))
#end addOSImage

#delete ISO information on OSImage.html
#function: deleteISOImages
@app.route('/deleteISOImages', methods=['POST'])
def deleteISOImages():
    try:
        if session.get('logged_in'):
            POST_ID = request.form['ISOIds'].split(',')
            for ID in POST_ID:
                query = db_session.query(SQLClass.os).filter(
                    SQLClass.os.osid == ID).first()
                try:
                    db_session.delete(query)
                    db_session.commit()
                except Exception as e:
                    db_session.rollback()
                    return json.dumps({'status': 'An Error occurred'})
            return json.dumps({'status': 'OK', 'Ids': POST_ID})
        else:
            return error('Unauthorized Access')
    except Exception as e:
        return json.dumps({'status': str(e)})
#end deleteISOImages

#upload config file related to iso on OSImage.html
#function: uploadOSCF
@app.route('/uploadOSCF', methods=['POST'])
def uploadOSCF():
    logging.debug('uploadOSCF() start')
    if session.get('logged_in'):
            try:
                if 'uploadCF' not in request.files:
                    logging.error("uploadOSCF() end when no file part.")
                    return json.dumps({'error': 'No file part'})
                file = request.files['uploadCF']
                if file.filename == '':
                    logging.error("uploadOSCF() end when no selected file.")
                    return json.dumps({'error': 'No selected file'})
                if file and allowed_file(file.filename,['xml', 'cfg']):
                    filename = secure_filename(file.filename)
                    logging.info('file name is %s' %(filename))
                    if filename[-3:] == 'xml' or filename[-3:] == 'cfg':
                        file.save(os.path.join(app.config['OS_CONFIG_FOLDER'], filename))
                    elif filename[-3:] == 'iso':
                        file.save(os.path.join(app.config['ISO_CKBASE_FOLDER'], filename))

                logging.debug('uploadOSCF() end')
                return json.dumps({'status': 'OK'})
            except Exception as e:
                logging.error('uploadOSCF() end when an error occurred:' + str(e))
                return json.dumps({'error': str(e)})
    else:
            logging.error('uploadOSCF() end when unauthorized access')
            return json.dumps({'error': 'Unauthorized Access'})

#end uploadOSCF

# get all the test case information from database
# and show them on the testcase.html table
# fucntion: getTestCases
@app.route('/getTestCases', methods=['GET'])
def getTestCases():
    logging.debug("getTestCases() start.")
    try:
        if session.get('logged_in'):
            query = db_session.query(SQLClass.testcase).order_by(
                    SQLClass.testcase.tcid)
            logging.info("Query data from testcase succeed.")
            records_dict = []
            for item in query.all():
                record_dict = {
                        'Id': item.tcid,
                        'Name': item.description,
                        'Description': item.bznumber,
                        'Platform': item.platform
                }
                records_dict.append(record_dict)
            logging.debug("getTestCases() end when dump json.")
            return json.dumps(records_dict)
        else:
            logging.error("getTestCases() end when unauthorized access.")
            return error('Unauthorized Access')
    except Exception as e:
            logging.error("getTestCases() end when an error occurred : " + str(e))
            return error(str(e))
# end getTestCases

def allowed_file(filename,array):
    ALLOWED_EXTENSIONS = set(array)
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#upload test case on testcase.html
#function: uploadTestCase
@app.route('/uploadTestCase', methods=['POST'])
def uploadTestCase():
    if session.get('logged_in'):
            try:
                if 'uploadTC' not in request.files:
                    return json.dumps({'error': 'No file part'})
                file = request.files['uploadTC']
                if file.filename == '':
                    return json.dumps({'error': 'No selected file'})
                if file and allowed_file(file.filename,['py', 'sh']):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['SCRIPT_FOLDER'], filename))
                return json.dumps({'status': 'OK'})
            except Exception as e:
                return json.dumps({'error': str(e)})
    else:
            return json.dumps({'error': 'Unauthorized Access'})

#end uploadTestCase

#add new test case information on testcase.html
#function: addTestCase
@app.route('/addTestCase', methods=['POST'])
def addTestCase():
    logging.debug("addTestCase() start.")
    try:
        if session.get('logged_in'):
            _description = request.form['Name']
            _bznumber = request.form['Description']
            _platform = request.form['Platform']
            new_record = SQLClass.testcase(
                description=_description,
                bznumber=_bznumber,
                platform=_platform
            )
            try:
                db_session.add(new_record)
                db_session.commit()
                logging.debug("addTestCase() end when dump json.")
                return json.dumps({'status': 'OK'})
            except Exception as e:
                db_session.rollback()
                if e.message.find("Duplicate entry") != -1:
                    flash(
                        message="Duplicated device found in database.",
                        category='warning')
                logging.error("addTestCase() end when an error occurred : " + str(e))
                return TestCase()
        else:
            logging.error("addTestCase() end when unauthorized access")
            return error('Unauthorized Access')
    except Exception as e:
        logging.error("addTestCase() end when an error occurred : " + str(e))
        return error(str(e))
#end addTestCase

#delete test case information on testcase.html
#function: deleteTestCases
@app.route('/deleteTestCases', methods=['POST'])
def deleteTestCases():
    logging.debug("deleteTestCases() start.")
    try:
        if session.get('logged_in'):
            POST_ID = request.form['TCIds'].split(',')
            for ID in POST_ID:
                query = db_session.query(SQLClass.testcase).filter(
                    SQLClass.testcase.tcid == ID).first()
                logging.info("Query data from testcase succeed.")
                try:
                    db_session.delete(query)
                    db_session.commit()
                except Exception as e:
                    db_session.rollback()
                    logging.error("deleteTestCases() end when an error occurred : " + str(e))
                    return json.dumps({'status': 'An Error occurred'})
            logging.debug("deleteTestCases() end when dump json.")
            return json.dumps({'status': 'OK', 'Ids': POST_ID})
        else:
            logging.error("deleteTestCases() end when unauthorized access.")
            return error('Unauthorized Access')
    except Exception as e:
        logging.error("deleteTestCases() end when an error occurred : " + str(e))
        return json.dumps({'status': str(e)})
#end deleteTestCases

# get all the task information from database
# and show them on the task.html table
# fucntion: getTasks
@app.route('/getTasks', methods=['GET'])
def getTasks():
    logging.debug("getTasks() start.")
    try:
        if session.get('logged_in'):
            db_session.commit()
            query = db_session.query(SQLClass.task).order_by(
                    SQLClass.task.taskid)
            logging.info("Query data from task succeed.")
            records_dict = []
            for item in query.all():
                record_dict = {
                        'Id': item.taskid,
                        'TaskType': item.taskType,
                        'TesterName': item.testerName,
                        'CrlServer': item.crlServer,
                        'SutMAC': item.sutMACaddress,
                        'MTSN': item.MTSN,
                        'OSVersion': item.OSVersion,
                        'OSImage': item.OSImage,
                        'kernelPKG': item.kernelPKG,
                        'Status': item.status
                }
                records_dict.append(record_dict)
            logging.debug("getTasks() end when dump json.")
            return json.dumps(records_dict)
        else:
            logging.error("getTasks() end when unauthorized access.")
            return error('Unauthorized Access')
    except Exception as e:
            logging.error("getTasks() end when an error occurred : " + str(e))
            return error(str(e))
# end getTasks


def getVersionFromImage(imageName):
    splitString = "-"
    OSversion = ""
    list = []

    if imageName:
        list = imageName.split(splitString)
        if list[0].lower() == "rhel":
            OSversion = list[0] + "-" + list[1] + "-" + list[2]
        elif list[0].lower() == "sle" and list[2][:2].upper() == "SP":
            OSversion = list[0] + "-" + list[1] + "-" + list[2] + "-" + list[len(list) - 2]
        elif list[0].lower() == "sle" and list[2][:2].upper() != "SP":
            OSversion = list[0] + "-" + list[1] + "-" + list[len(list) - 2]
        elif list[0].lower() == "vmware" :
            OSversion = list[0] + "-" + list[3] + "-" + list[4][:list[4].find('.x86')]
        else:
            OSversion = "This os is not supported"
    else:
        OSversion = "image name is null"
    logging.info("OSversion is : " + OSversion)
    return OSversion

def parseScript(scriptSet):
    _scriptList = []
    _cmdList = []
    _suffix =""
    splitString = ','

    if scriptSet:
        _cmdList = scriptSet.split(splitString)
        for _cmdName in _cmdList:
            suffix = _cmdName[len(_cmdName)-2:]
            if suffix == "sh":
                _cmdPath = "sh "+ app.config['SCRIPT_FOLDER_SUT'] + "/" + _cmdName
            elif suffix == "py":
                _cmdPath = "python " + app.config['SCRIPT_FOLDER_SUT'] + "/" + _cmdName
            else :
                _cmdPath = ""
            if _cmdPath :
                _scriptList.append(_cmdPath)
    logging.info("_scriptList is " + _scriptList)
    return _scriptList

def createCfg(request,taskId):
    _cfgList = {}
    _scriptList = []
    _PubIPAddress = request.form['PubIPAddress']
    _taskType = request.form['taskType']
    _sutMACaddress = request.form['sutMACaddress']
    _MTSN = request.form['MTSN']
    _PriIPAddress = request.form['PriIPAddress']
    _OSImage = request.form['OSImage']
    _kernelPKG = request.form['kernelPKG']
    _OSVersion = getVersionFromImage(_OSImage)
    _scriptSet = request.form['scriptList']

    #make filename and _cfgList
    _cfgList.clear()
    if _taskType == "OS deployment":
        _fileName = "OSDeploy_" + _PubIPAddress + "_" + taskId + ".cfg"
        _cfgList[model.cfgEnum.MAC] = _sutMACaddress
        _cfgList[model.cfgEnum.MTSN] = _MTSN
        _cfgList[model.cfgEnum.SERVER_IP] = _PriIPAddress
        _cfgList[model.cfgEnum.OS_VERSION] = _OSVersion
    elif _taskType == "Feature test":
        _fileName = "Feature_" + _PubIPAddress + "_" + taskId + ".cfg"
        _cfgList[model.cfgEnum.MAC] = _sutMACaddress
        _cfgList[model.cfgEnum.MTSN] = _MTSN
        _cfgList[model.cfgEnum.SERVER_IP] = _PriIPAddress
        _cfgList[model.cfgEnum.OS_VERSION] = _OSVersion
    else :
        _fileName = "Inbox_" + _PubIPAddress + "_" + taskId + ".cfg"
        os_name=_OSImage.partition('-')[0]
        if os_name.lower() == "vmware":
            _cfgList[model.cfgEnum.OS_IMAGE] = _OSImage
            #_cfgList[model.cfgEnum.KER_RPM] = _kernelPKG
        else:
            _cfgList[model.cfgEnum.OS_IMAGE] = _OSImage
            _cfgList[model.cfgEnum.KER_RPM] = _kernelPKG


    _fileName = app.config['TASK_CONFIG_FOLDER'] + "/" + _fileName
    logging.info("config file name is " + _fileName)
    #TBD delete configfile
    #write cfg
    fl = open(_fileName, 'a+')
    logging.info("open file succeed.")

    for key in _cfgList.keys():
        fl.write(key + '\n')
        fl.write(_cfgList.get(key, "") + '\n')

    if _taskType == "Feature test":
        _scriptList = parseScript(_scriptSet)
        _extraScript = "echo \"Scp_status\" >> " + app.config['SCRIPT_FOLDER_SUT'] + "/scp_cli.sh"
        fl.write(model.cfgEnum.TEST_CASE + '\n')
        if _scriptList:
            for script in _scriptList:
                fl.write(script + '\n')
        fl.write(_extraScript + '\n')
    logging.info("write file succeed.")

    fl.close()
    logging.info("close file succeed.")

def getCfg(directory,taskId):
    splitString = '_'
    try:
        fileList = os.listdir(directory)
        for file in fileList:
            if os.path.isfile(os.path.join(directory,file)):
                index = file.rfind(splitString, 0, len(file))
                #take taskID from xxx_taskID.cfg
                if index != -1:
                    ID = file[index + 1:len(file) - 4]
                    if ID == taskId:
                        logging.info("getCfg() end ")
                        return file
    except Exception as e:
        #do nothing
        logging.error("getCfg() end when an error occurred : " + str(e))
        # error(str(e))
        return ""

def deleteCfg(taskId):
    fileName = getCfg(app.config['TASK_CONFIG_FOLDER'],taskId)
    if fileName != "":
        os.remove(os.path.join(app.config['TASK_CONFIG_FOLDER'],fileName))

#add new task and create new config on task.html
#function: addTask
@app.route('/addTask', methods=['POST'])
def addTask():
    logging.debug('addTask() start')
    try:
        if session.get('logged_in'):
            hasPCIID = False
            taskID = "-1"
            _taskType = request.form['taskType']
            _testerName = request.form['testerName']
            _crlServer = request.form['crlServer']
            _sutMACaddress = request.form['sutMACaddress']
            _MTSN = request.form['MTSN']
            _OSVersion = getVersionFromImage(request.form['OSImage'])
            _OSImage=request.form['OSImage']
            _kernelPKG=request.form['kernelPKG']
            _status=request.form['status']

            if(_taskType == "Inbox test"):
                logging.debug("task status is %s" % hasPCIID)
                PCIID_fileList = os.listdir(app.config['PCIID_CKBASE_FOLDER'])
                for file in PCIID_fileList:
                    if _OSImage[:_OSImage.find('-')].lower() == "vmware":
                        if os.path.isfile(os.path.join(app.config['PCIID_CKBASE_FOLDER'], file)):
                            flag_1 = _OSImage.partition('Installer-')[2]
                            flag_2 = _OSImage.find('update')
                            if flag_2 == -1:
                                os_version = flag_1[:flag_1.find('-')]
                            else:
                                os_version = flag_1[:flag_1.find('.update')]
                            TXT_filelist = os.listdir(model.driverDir + 'VMware/' + os_version + '/')
                            TXT_file = _OSImage + '.txt'
                            if TXT_file in TXT_filelist:
                                    hasPCIID = True
                                    break
                    else:
                        if os.path.isfile(os.path.join(app.config['PCIID_CKBASE_FOLDER'], file)):
                            hasPCIID = True
                            break

                if(hasPCIID == False):
                    logging.debug('addTask() end when no PCIID file.')
                    return json.dumps({'status': 'NG', 'detail': 'need PCIID file'})
            new_record = SQLClass.task(
                taskType=_taskType,
                testerName=_testerName,
                crlServer=_crlServer,
                sutMACaddress=_sutMACaddress,
                MTSN=_MTSN,
                OSVersion=_OSVersion,
                OSImage=_OSImage,
                kernelPKG=_kernelPKG,
		        status=_status
            )
            try:
                db_session.add(new_record)
                db_session.commit()
                query = db_session.query(SQLClass.task).order_by(-SQLClass.task.taskid).first()
                taskID = query.taskid
                osimage=query.OSImage
                thread=threading.Thread(target=taskStatus,args=(taskID,osimage))
                thread.start()
                createCfg(request,str(taskID))
                logging.debug('addTask() end when dump json.')
                return json.dumps({'status': 'OK'})
            except Exception as e:
                db_session.rollback()
                if taskID != "-1":
                    deleteCfg(taskID)
                if e.message.find("Duplicate entry") != -1:
                    flash(
                        message="Duplicated device found in database.",
                        category='warning')
                logging.debug('An error occurred :'+str(e))
                return task()
        else:
            logging.debug('An error occurred : Unauthorized Access')
            return error('Unauthorized Access')
    except Exception as e:
        logging.error('An error occurred : '+str(e))
        return error(str(e))
#end addTask

#delete task information on task.html
#function: deleteTasks
@app.route('/deleteTasks', methods=['POST'])
def deleteTasks():
    logging.debug("deleteTasks() start.")
    try:
        if session.get('logged_in'):
            POST_ID = request.form['TaskIds'].split(',')
            for ID in POST_ID:
                query = db_session.query(SQLClass.task).filter(
                    SQLClass.task.taskid == ID).first()
                logging.info("Query data from task succeed.")
                try:
                    db_session.delete(query)
                    db_session.commit()
                    deleteCfg(ID)
                except Exception as e:
                    db_session.rollback()
                    logging.error("deleteTasks() end when an error occurred : " + str(e))
                    return json.dumps({'status': 'An Error occurred'})
            logging.error("deleteTasks() end when dump json.")
            return json.dumps({'status': 'OK', 'Ids': POST_ID})
        else:
            logging.error("deleteTasks() end when unauthorized access.")
            return error('Unauthorized Access')
    except Exception as e:
        logging.error("deleteTasks() end when an error occurred : " + str(e))
        return json.dumps({'status': str(e)})
#end deleteTasks

#download config file on task.html
#function: getConfigById
@app.route('/getConfigById', methods=['POST'])
def getConfigById():
    logging.debug("getConfigById() start.")
    try:
        if session.get('logged_in'):
            POST_ID = request.form['taskid']
            fileName = getCfg(app.config['TASK_CONFIG_FOLDER'], POST_ID)
            fopen = open(os.path.join(app.config['TASK_CONFIG_FOLDER'],fileName), 'r')
            logging.info("open file succeed.")
            content = fopen.readlines()
            logging.info("read file succeed.")
            fileObject = [{'fileName': fileName,
                            'content':content
                            }]
            fopen.close()
            logging.debug("getConfigById() end when dump json.")
            return json.dumps(fileObject)
        else:
            logging.error("getConfigById() end when unauthorized access.")
            return error('Unauthorized Access')
    except Exception as e:
        logging.error("getConfigById() end when an error occurred : " + str(e))
        return error(str(e))
#end getConfigById


#change task status
def taskStatus(TASKID,OSIMAGE):
    file_name = OSIMAGE[:-4] + '_' + str(TASKID) + '.xlsx'
    list = OSIMAGE.split('-')
    if list[0].lower() == "rhel":
        seach_directory = model.driverDir + 'RedHat/' + list[1] + '/'
    elif list[0].lower() == "sle" and list[2][:2].upper() == "SP":
        seach_directory = model.driverDir + 'SUSE/' + list[1] + '.' + list[2][2:] + '/'
    elif list[0].lower() == "sle" and list[2][:2].upper() != "SP":
        seach_directory = model.driverDir+ 'SUSE/' + list[1] + '/'
    elif list[0].lower() == 'vmware' and OSIMAGE.find('update') == -1:
        seach_directory = model.driverDir + 'VMware/' + list[3] + '/'
    elif list[0].lower() == 'vmware' and OSIMAGE.find('update') != -1:
        seach_directory = model.driverDir + 'VMware/' + list[3][:list[3].find('.update')] + '/'
    else:
        seach_directory = model.driverDir
    logging.debug('update status start path is %s' % seach_directory)
    try:
        query = db_session.query(
            SQLClass.task).filter(SQLClass.task.taskid == TASKID).first()
        if query.taskType == 'Inbox test':
            try:
                for run_time in range(0,61):
                    if run_time < 60:
                        all_files = os.listdir(seach_directory)
                        if file_name in all_files:
                            lock.acquire()
                            query.status = TASK_STATUS_SUCESS
                            db_session.commit()
                            lock.release()
                            logging.info('update status completed')
                            break
                        else:
                            time.sleep(10)
                    else:
                        lock.acquire()
                        query.status = TASK_STATUS_FAILED
                        db_session.commit()
                        lock.release()
                        logging.info('update status failed')
                        break
            except Exception as e:
                db_session.rollback()
                logging.error('update status failed :' + str(e))
    except Exception as e:
        logging.error('update status failed : ' + str(e))
#end change task status


#main fucntion
if __name__ == "__main__":

    host_ip = 'ais.labs.lenovo.com'
    host_port = 8000
    app.run(debug=True, host=host_ip, port=host_port)
    '''
    app.run(debug=True)
    '''
