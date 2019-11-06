#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on Jan 18, 2018
daemon_class.py: autotest daemon class file
@author: Neo
Vesion: 1.0
'''

import sys, os, time, atexit, signal


class Daemon:
    def __init__(self,
                 pidfile='/tmp/daemon.pid',
                 stdin='/dev/null',
                 stdout='dev/null',
                 stderr='/dev/null',
                 umask=022,
                 verbose=1):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.umask = umask
        self.verbose = verbose
        self.daemon_alive = True

    def daemonize(self):
        if os.path.exists(self.pidfile):
            raise RuntimeError('Already Running.')
        # First time fork (detached from parent)
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed:(%d) %s\n" % (e.errno,
                                                           e.strerror))
            sys.exit(1)

        os.chdir('/')
        os.setsid()
        os.umask(self.umask)

        # Second time fork (relinquish session leadership)
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write('fork #2 failed: (%d) %s\n' % (e.errno,
                                                            e.strerror))
            sys.exit(1)

        # Flush I/O buffers
        sys.stdout.flush()
        sys.stderr.flush()

        # Replace file descriptors for stdin, stdout and stderr
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        def sig_handler(signum, frame):
            self.daemon_alive = False

        signal.signal(signal.SIGTERM, sig_handler)
        signal.signal(signal.SIGINT, sig_handler)

        if self.verbose >= 1:
            print 'daemon process started...'

        # Arrange to have the PID file removed on exit/signal
        atexit.register(self.delpid)
        # Wrtie the PID file
        pid = str(os.getpid())
        file(self.pidfile, 'w').write('%s\n' % pid)

    def getpid(self):
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        except SystemExit:
            pid = None
        return pid

    def delpid(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def start(self):
        if self.verbose >= 1:
            print 'ready to starting....'
        # check for the pid file to see if the daemon already running
        pid = self.getpid()
        if pid:
            message = "pidfile %s already exist. Daemon already running\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)
        # start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        if self.verbose >= 1:
            print 'stopping ...'
        pid = self.getpid()
        if not pid:
            message = "pidfile [%s] does not exist. Daemon not running.\n"
            sys.stderr.write(message % self.pidfile)
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)
            return
        # try to kill the daemon process
        try:
            i = 0
            while True:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
                i += 1
                if i % 10 == 0:
                    os.kill(pid, signal.SIGHUP)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)
            if self.verbose >= 1:
                print 'Stopped!'

    def restart(self):
        self.stop()
        self.start()

    def is_running(self):
        pid = self.getpid()
        return pid and os.path.exists('/proc/%d' % pid)

    def run(self):
        print 'base class run()'
