#!/usr/bin/env python

import sys, os, urllib2, csv, json, threading, Queue, time

#global for all threads to use.
queue = Queue.Queue()


def fixAlexaFail(url):
    if 'http://' not in url:
        return "http://%s/" % (url)


# urllib2 redirection is traditionally silent. --we need this to grab the status code.
class SmartRedirectHandler(urllib2.HTTPRedirectHandler):     
    def http_error_301(self, req, fp, code, msg, headers):  
        result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)              
        result.status = code                                 
        return result                                       

    def http_error_302(self, req, fp, code, msg, headers):   
        result = urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)              
        result.status = code                                
        return result

class URLThread(threading.Thread):
    standardUserAgent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.102 Safari/534.13'
    mobileUserAgent = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_1 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8B117 Safari/6531.22.7'
    def __init__(self, urls, queue):
        threading.Thread.__init__(self)
        self.urls = urls
        self.queue = queue

    def run(self):
        for row in self.urls:
            id = row[0]
            url = row[1]
            dRequest = urllib2.Request(url, None, {'User-Agent': self.standardUserAgent})
            dOpener = urllib2.build_opener(SmartRedirectHandler())

            mRequest = urllib2.Request(url, None, {'User-Agent': self.mobileUserAgent})
            mOpener = urllib2.build_opener(SmartRedirectHandler())

            try:
                # timeout of 30 seconds... cuz right now it is taking for frikkin ever.
                dResult = dOpener.open(dRequest, None, 10)
                mResult = mOpener.open(mRequest, None, 10)
            except:
                # ruh roh... we had an error with the url itself. Let's just return that we don't know what's up.
                self.queue.put((dict(id=id, url=url, hasMobile=False, location='Error', redirected=False, status='Error'))
                continue

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
                # only 301's and 302's get proper status codes back.
                status = '200'
            
            
            self.queue.put(dict(id=id, url=url, hasMobile=hasMobile, location=location, redirected=redirected, status=status))

    

help_message = '''
This script tests whether or not sites have a mobile version
    -h / --help     show this text
    -q / --quiet    don't print to console
    -o / --output=  File you want the output data to go (default: results.out)
    -t / --type=    Putput data type (csv, json - default: json)
    -f / --fetch    Fetch new list
    -i / --input=   Specify a different input filename (default: top-1m.csv)
    -n / --numhosts=  Number of top hosts's to test. (default: 1000)
    -T / --threads= Specify number of worker threads to spawn (default: 10)
'''


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hqo:t:fi:n:T:", ["help", "quiet", "output=", "type=", "fetch", "input=", "numhosts=", "threads="])
        except getopt.error, msg:
            raise Usage(msg)
        quiet = False
        output = 'results.out'
        outType = 'json'
        fetch = False
        inputFile = 'top-1m.csv'
        numhosts = 1000
        threads = 10
        
        # option processing
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-q", "quiet"):
                quiet = True
            if option in ("-o", "--output"):
                output = value
            if option in ("-t", "--type"):
                if value in ('csv', 'json'):
                    outType = value                    
            if option in ("-f", "--fetch"):
                fetch = True
            if option in ("-i", "--input"):
                inputFile = value
            if option in ("-n", "--numhosts"):
                numhosts = int(value) if int(value) < 1000001 else 1000000
            if option in ("-T", "--threads"):
                threads = value


        #start of real codez


        # get urls to test from input file
        alexaTopMillion = csv.reader(open(inputFile, 'rb'))
        count = 0
        urls = []
        for row in alexaTopMillion:
            urls.append([row[0], fixAlexaFail(row[1])])
            count += 1
            if count == numhosts:
                break
        
        
        # call sub threads breaking up list for each
        threads = min([threads, len(urls)])
        start = time.time()
        print """Started testing urls at %s
This determines whether or not a domain
has a mobile version.

Threads: %d
Input: %s
Output: %s
Quantity: %d
""" % (start, threads, inputFile, output, len(urls),)
        myThreads = []
        section_amount = len(urls)/threads
        for i in range(threads):
            t = URLThread(urls[threads*section_amount:threads*section_amount+section_amount], queue,)
            t.setDaemon(True)
            t.run()
            t.append(myThread)
        
        results = []
        
        while len(results) < numhosts:
            if not queue.empty():
            result = queue.get()
            results.append(result)
            if not quiet:
                print "%s\n\t%s - %s\n" % (result['url'],
                    'yes' if result['hasMobile'] else 'no',
                    result['status'] if result['location'] == result['url'] else "%s -> %s" % (result['status'], result['location'],))
            queue.task_done()
            time.sleep(1)
        
        # well, we have enough data, let's just make sure all the threads are dead.
        for t in myThreads:
            t.stop()
        print "Elapsed Time: %s" % (time.time() - start)
        # sort through the results, put them back in order, and write them to a file.
        if outType == 'json':
            out = open(output, 'w') 
            out.write(json.dumps(sorted(results, key=lambda k: k['id'])))            
            return 0
        writer = csv.DictWriter(open(output, 'w'))
        writer.writerows(sorted(results, key=lambda k: k['id']))
        return 0

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())
