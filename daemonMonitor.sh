#!/bin/sh
daemonDir=/opt/lenovo/AIS/www/DataServer

autotestd=`ps -ef |grep daemon_autotest.py |grep -v grep`
#echo ${autotestd}
if [ -z "${autotestd}" ];then
	python ${daemonDir}/daemon_autotest.py start
fi

autoPackaged=`ps -ef |grep daemon_autoPackage.py | grep -v grep`
#echo ${autoPackaged}
if [ -z "${autoPackaged}" ];then
	python ${daemonDir}/daemon_autoPackage.py start
fi

isoSyncd=`ps -ef |grep daemon_isoimageSync.py | grep -v grep`
#echo ${isoSyncd}
if [ -z "${isoSyncd}" ];then
	python ${daemonDir}/daemon_isoimageSync.py start
fi

configSync=`ps -ef |grep daemon_configfileSync.py | grep -v grep`
#echo ${configSync}
if [ -z "${configSync}" ];then
	python ${daemonDir}/daemon_configfileSync.py start
fi

testcaseSync=`ps -ef |grep daemon_testcaseSync.py | grep -v grep`
#echo ${testcaseSync}
if [ -z "${testcaseSync}" ];then
	python ${daemonDir}/daemon_testcaseSync.py start
fi

