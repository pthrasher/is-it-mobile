#!/usr/bin/env python

import sys, os, urllib2, csv, json

# change this to how many IP's you want to test. cannot be greater than 1 million.
IPS_TO_TEST = 1000


def yesno(test):
    if test:
        return 'yes'
    return 'no'

def fixAlexaFail(url):
    if 'http://' not in url:
        return "http://%s/" % (url)

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):     
    def http_error_301(self, req, fp, code, msg, headers):  
        result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)              
        result.status = code                                 
        return result                                       

    def http_error_302(self, req, fp, code, msg, headers):   
        result = urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)              
        result.status = code                                
        return result

class URLHandler():
    standardUserAgent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.102 Safari/534.13'
    mobileUserAgent = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_1 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8B117 Safari/6531.22.7'
    def __init__(self, urlList=['http://www.google.com/']):
        self.urlList = urlList
        
    def checkurlList(self):
        for url in self.urlList:
            dRequest = urllib2.Request(url, None, {'User-Agent': self.standardUserAgent})
            dOpener = urllib2.build_opener(SmartRedirectHandler())

            mRequest = urllib2.Request(url, None, {'User-Agent': self.mobileUserAgent})
            mOpener = urllib2.build_opener(SmartRedirectHandler())

            try:
                dResult = dOpener.open(dRequest)
                mResult = mOpener.open(mRequest)
            except:
                # ruh roh... we had an error with the url itself. Let's just return that we don't know what's up.
                yield dict(url=url, hasMobile=False, location='Error', redirected=False, status='Error')

            hasMobile = True
            if dResult.read() == mResult.read():
                hasMobile = False

            location = url
            try:
                redirected = False
                if mResult.status in ['301', '302']:
                    redirected = True
                location = mResult.url
                status = mResult.status
            except AttributeError:
                status = '200'
                

            yield dict(url=url, hasMobile=hasMobile, location=location, redirected=redirected, status=status)
            
if __name__ == '__main__':
    print "Are they mobile? (getting alexa top 1,000)"

    alexaTopMillion = csv.reader(open('top-1m.csv', 'rb'))
    count = 0
    alexaTop1k = []
    for row in alexaTopMillion:
        alexaTop1k.append(fixAlexaFail(row[1]))
        count += 1
        if count == IPS_TO_TEST:
            break

    urlh = URLHandler(urlList=alexaTop1k)
    # urlh = URLHandler(urlList=['http://www.endgames.us/', 'http://www.iptrust.com/'])
    results = []
    for answer in urlh.checkurlList():
        results.append(answer)
        print "%s\n\t%s - %s\n" % (answer['url'], yesno(answer['hasMobile']), answer['status'] if answer['location'] == answer['url'] else "%s -> %s" % (answer['status'], answer['location'],))
    out = open('results.out', 'w')
    out.write(json.dumps(results))