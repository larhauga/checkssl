#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from time import sleep
# from multiprocessing import Process
import pprint
import datetime

from Queue import Queue
from threading import Thread

API_BASE='https://api.ssllabs.com/api/v2/'
API_INFO='https://api.ssllabs.com/api/v2/info'
OUTFILE='/tmp/output.json'

class Worker(Thread):
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception, e:
                print "In run exception"
                print e
            self.tasks.task_done()

class ThreadPool:
    def __init__(self, num_threads):
        self.tasks= Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        self.tasks.join()


def api_available():
    r = requests.get(API_INFO)
    if r.status_code == 200:
        if r.json()['engineVersion']:
            return True
    return False

def api_limit_reached():
    """Finds out if api limit is reached"""
    r = requests.get(API_INFO)
    if r.status_code == 200:
        data = r.json()
        try:
            if int(data['maxAssessments']) > int(data['currentAssessments']):
                print "Current assessments: %s/%s" % (str(data['currentAssessments']), str(data['maxAssessments']))
                return False
            else:
                print "Current assessments in progress: %s/%s" % (str(data['currentAssessments']), str(data['maxAssessments']))
                return True
        except:
            print "Parse data error: {}".format(str(data))

def api_current():
    r = requests.get(API_INFO)
    if r.status_code == 200:
        return r.json()['currentAssessments']

def api_limit_free():
    r = requests.get(API_INFO)
    if r.status_code == 200:
        d = r.json()
        return int(d['maxAssessments']) - int(d['currentAssessments'])

def analyze(url):
    """Trigger analyze api"""
    r = requests.get('{}analyze?host={}&all=on&ignoreMismatch=on&fromCache=on'.format(API_BASE,url))
    if r.status_code == 200:
        data = r.json()
        return data


def process_domain(domain, n=None):
    """Trying to process domain. do 5 checks if api busy"""
    if not api_limit_reached() and n<5:
        print "starting to analyze domain %s" % domain
        test = analyze(domain)
        if test['status'] == 'READY':
            # TODO: Switch to use logger instead, meant for splunk
            with open(OUTFILE, 'a') as f:
                f.write("%s\n" %(json.dumps(test)))
        while test['status'] != 'READY':
            print "Wating for %s" % domain
            sleep(1)
            test = analyze(domain)
            if test['status'] == 'READY':
                with open(OUTFILE, 'a') as f:
                    f.write("%s\n" % (json.dumps(test)))
                    print "Done for %s" % (domain)
            sleep(19)
    else:
        if n:
            n = n + 1
        else:
            n = 1
        sleep(1)
        process_domain(domain, n)

def find_domains():
    # TODO: Fix up
    ip_ranges= ['']
    from netaddr import IPNetwork
    import socket
    domains = []
    # TODO: Loop over ip ranges as well
    for ip in list(IPNetwork(ip_ranges[0])):
        # print ip
        try:
            domains.append(socket.gethostbyaddr(str(ip))[0])
        except socket.herror:
            print "Unkown host %s" % ip
        except socket.gaierror:
            pass
            #print "Name or service not known %s" % ip
    # print domains
    return domains

def main():
    check_list = []

    #check_list = find_domains()
    available = api_available()
    if not available:
        print "API not currently available. Waiting 60 secs. Trying for an hour"
        count = 1
        while count < 60 and not available:
            count = count + 1
            sleep(60)
            available = api_available()

    pool = ThreadPool(api_limit_free()-1)

    for i, dom in enumerate(check_list):
        print 'Batch start progress: %.2f%c' % ((float(i)/float(len(check_list)))*100.0,'%')
        pool.add_task(process_domain, dom)
        sleep(2)

    pool.wait_completion()

if __name__ == '__main__':
    main()
