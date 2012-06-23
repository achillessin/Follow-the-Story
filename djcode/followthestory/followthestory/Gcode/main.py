import pyGTrends as ptrends
from numpy import *
from csv import DictReader
import matplotlib.pyplot as plt
import smooth
import constants
from xgoogle.search import GoogleSearch, SearchError
import matplotlib
import os.path
import os
import datetime


#class for objects of URL,DESC,DATE,TITLE
class Article:
    def __init__(self,title,url,desc,date=None,ddate=None):
        self._title=title
        self._url=url
        self._desc=desc
        self._date=date
        self._ddate=ddate
        self._shares=None
        
    def printArticle(self):
        print self._title
        print self._desc
        print self._url
        print self._date
        print
        
    def get_url(self):
        return self._url
    def get_title(self):
        return self._title
    def get_desc(self):
        return self._desc
    def get_date(self):
        return self._date
    def get_ddate(self):
        if self._ddate==None:
            return datetime.date.today()
        else:
            return self._ddate
    def get_shares(self):
        return self._shares
    def set_shares(self,s):
        self._shares=s
    
#class Scrape to query and retrieve
class Scrape:
    def __init__(self,username,password):
        self._r = ptrends.pyGTrends(constants.Username, constants.Password)

    def getArticles(self,query,datetuple,location=constants.Geo):
        Articlelist=list()
        gs=GoogleSearch(query)
        gs._results_per_page = 10 #(default,dont change)
        #get date period
        start=datetuple[0]
        end=datetuple[1]
        month=constants.months[start[0:3]]
        year=int(start[-4:])
        day=int(start[4:-5])
        gs._set_start_date(month,day,year)
        month=constants.months[end[0:3]]
        year=int(end[-4:])
        day=int(end[4:-5])
        gs._set_end_date(month,day,year)
        #print month,day,year
        results = gs.get_results()
        
        for res in results:
            if(res.date == None):
                a=Article(res.title.encode('utf8'),res.url.encode('utf8'),res.desc.encode('utf8'),res.date)
            else:
                s=res.date.replace(',',' ').split()
                a=Article(res.title.encode('utf8'),res.url.encode('utf8'),res.desc.encode('utf8'),res.date,datetime.date(int(s[2]),constants.months[s[0]],int(s[1])))
            Articlelist.append(a)
        print '0'
        for i in range(1,constants.pagecount):
            gs._set_page(i)
            results = gs.get_results()
            for res in results:
                if(res.date == None):
                    a=Article(res.title.encode('utf8'),res.url.encode('utf8'),res.desc.encode('utf8'),res.date)
                else:
                    s=res.date.replace(',',' ').split()
                    a=Article(res.title.encode('utf8'),res.url.encode('utf8'),res.desc.encode('utf8'),res.date,datetime.date(int(s[2]),constants.months[s[0]],int(s[1])))
                Articlelist.append(a)
            print i
        return Articlelist

    def query(self,query,location=constants.Geo,graph=True,startdate=None,enddate=None):
        self._r.download_report(query,date='all',geo=location,geor='all',graph='all_csv',sort=0,scale=constants.FixedScale,sa='N')

        d = DictReader(self._r.csv().split('\n'))
        data=[row for row in d]
        week_data=[ (item["Week"]) for item in data]
        search_data=[ (item[" " + query]) for item in data]

        ##print search_data
        search_data=[ s.replace(' ','') for s in search_data]
        search_data=[int(float(x)*100) for x in search_data]
        search_data=array(search_data)
        #smooth
        #find max
        c = (diff(sign(diff(search_data))) < 0).nonzero()[0] + 1 # local max
        mean_c=mean(search_data[c])
        std_c=std(search_data[c])
        c= [ x for x in c if search_data[x]>(mean_c+1.5*std_c)]
        if graph is True:
            matplotlib.rc('xtick', labelsize=6) 
            plt.plot(range(0,len(search_data)),search_data)
            plt.plot(c,search_data[c],"o",label="max")

    
        #to find period around the peak, find the values 5% or less away from peak
        date_range=list()
        for i in range(0,len(c)):
            tup=()
            cur_l=c[i]
            cur_r=c[i]
            #check left
            while True:
                if (search_data[cur_l]>0.05*search_data[c[i]]):
                    if cur_l>0:
                        cur_l=cur_l-1
                    else:
                        break
                else:
                    break
            #check right
            while True:
                if (search_data[cur_r]>0.05*search_data[c[i]]):
                    if cur_r<len(search_data)-1:
                        cur_r=cur_r+1
                    else:
                        break
                else:
                    break
            #take the cur_l and cur_r and add it to the date_range list
            tup=(cur_l,cur_r)
            date_range.append(tup)
            #print 'peak',c[i],' ','left',cur_l,' ','right',cur_r
            if graph is True:            
                plt.plot(cur_l,search_data[cur_l],"^")
                plt.plot(cur_r,search_data[cur_r],"^")
                plt.xticks( range(0,len(search_data))[0::20], week_data[0::20],rotation='vertical')
        if graph is True:
            plt.title('Search index for query: '+query)
            plt.xlabel('Date')
            plt.ylabel('search index')
            if os.path.isfile(constants.graphfile):
                os.remove(constants.graphfile)
            plt.savefig(constants.graphfile)
            plt.clf()
        #now date_ranges has indices of the date periods in Week_data
        #if start and end dates are None, get the peak closes to current date i.e last peak
        datetuple=(week_data[date_range[-1][0]],week_data[date_range[-1][1]])
        Articlelist=self.getArticles(query,datetuple,location)

        return Articlelist

    
