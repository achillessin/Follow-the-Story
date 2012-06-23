import httplib
import json
import logging
import socket
import time
import urllib
import urllib2
import constants
import matplotlib.pyplot as plt
import os

CLASSIFY_TWEETS_URL="http://twittersentiment.appspot.com/api/bulkClassifyJson"
SEARCH_HOST="search.twitter.com"
SEARCH_PATH="/search.json"


class TagCrawler(object):
    
    def __init__(self, max_id, tag, interval):
        self.max_id = max_id
        self.tag = tag
        self.interval = interval
        
    def search(self,page):
        print 'page',page
        c = httplib.HTTPConnection(SEARCH_HOST)
        params = {'q' : self.tag}
        self.max_id=None
        if self.max_id is not None:
            params['since_id'] = self.max_id
        path = "%s?%s" %(SEARCH_PATH, urllib.urlencode(params))
        path = path + "&lang=en&rpp=100&page="+str(page)
        print path
        try:
            c.request('GET', path)
            r = c.getresponse()
            data = r.read()
            c.close()
            try:
                result = json.loads(data)
            except ValueError:
                return None
            if 'results' not in result:
                return None
            self.max_id = result['max_id']
            print len(result['results']),'result'
            return result['results']
        except (httplib.HTTPException, socket.error, socket.timeout), e:
            logging.error("search() error: %s" %(e))
            print e
            return None

    def loop(self):
        while True:
            logging.info("Starting search")
            data = self.search()
            if data:
                logging.info("%d new result(s)" %(len(data)))
                self.submit(data)
            else:
                logging.info("No new results")
            logging.info("Search complete sleeping for %d seconds"
                    %(self.interval))
            time.sleep(float(self.interval))

    def submit(self, data):
        pass
    #positive,negative,neutral=twitterfeed.classify(tfeed)    
    def classify(self,results):
        positive=0
        neutral=0
        negative=0
        tlist=list()
        print len(results)
        tdict={"data":tlist}
        for i in range(0,len(results)):
            tlist.append({"text":results[i]})
        jdata=json.dumps(tdict,encoding='utf8')
        dat=urllib2.urlopen(CLASSIFY_TWEETS_URL,jdata)
        dic=json.load(dat,encoding='latin-1')
        ls=dic['data']
        for i in range(0,len(ls)):
            if ls[i]["polarity"]==constants.neutral :
                neutral = neutral +1
            if ls[i]["polarity"]==constants.positive :
                positive = positive +1
            if ls[i]["polarity"]==constants.negative :
                negative = negative +1
        #save plot
        plt.bar([1,2],[positive,negative],width=(0.2,0.2),color=['green','red']);
        plt.xticks([1,2],['positive','negative'])
        plt.xlabel('Reaction')
        plt.ylabel('Number')
        if os.path.isfile(constants.twittergraphfile):
                os.remove(constants.twittergraphfile)
        plt.savefig(constants.twittergraphfile)
        plt.clf()
        return positive,negative,neutral
