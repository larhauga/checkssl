#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from time import sleep
from multiprocessing import Process
import pprint
import datetime

API_BASE='https://api.ssllabs.com/api/v2/'
API_INFO='https://api.ssllabs.com/api/v2/info'

OUTFILE='output.json'

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
                print data['currentAssessments']
                return True
            else:
                print data['currentAssessments']
                return False
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

def endpoint(endpoint):
    endpoint['details']
    'grade'


def process_domain(domain):
    test = analyze(domain)
    if test['status'] == 'READY':
        with open(OUTFILE, 'a') as f:
            f.write("%s\n" %(json.dumps(test)))
    while test['status'] != 'READY':
        sleep(1)
        test = analyze(domain)
        if test['status'] == 'READY':
            with open(OUTFILE, 'a') as f:
                f.write("%s\n" % (json.dumps(test)))
                print "Done for %s" % (domain)
        sleep(19)

def burst(domains):
    threads = []
    for domain in domains:
        thread = Thread(target=process_domain, args=domain)
        thread.start()
        threads.append(thread)

    for t in threads:
        t.join()

def gen_threads(domains):
    threads = []
    for domain in domains:
        thread = Thread(target=process_domain, args=domain)
        threads.append(thread)

    return threads

def main():
    check_list = []
    if api_available():
        for domain in check_list:
            print "Testing domain %s" % domain
            process_domain(domain)
        print api_limit_reached()
    else:
        print "api not available"

if __name__ == '__main__':
    main()
