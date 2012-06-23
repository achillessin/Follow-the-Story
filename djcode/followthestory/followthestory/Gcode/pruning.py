from main import Article,Scrape
import constants
import urllib2
import json
import datetime
import re
import time
import numpy as np
import matplotlib.pyplot as plt

month_list = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

def facebook_likes(link):
#Getting Facebook shares/recommendations
    graph_link = "http://graph.facebook.com/?ids="
    req = urllib2.Request( graph_link + link)
    try:
        response = urllib2.urlopen( graph_link + link )
        html = response.read()
    except urllib2.HTTPError,e:
        return 0
    
    i = re.search('shares":(\d+)',html)

    if i is not None:
        no_of_shares_raw = i.group(0)
    else:
        return 0
    
    j = re.search('(\d+)', no_of_shares_raw)
    if j is not None:
        no_of_shares = int(j.group())
    else:
        return 0

    return no_of_shares

#Counting twitter retweets
def twitter_likes(link):
    twitter_link = "http://urls.api.twitter.com/1/urls/count.json?url="
    req = urllib2.Request( twitter_link + link)
    try:
        response = urllib2.urlopen( twitter_link + link )
        html = response.read()
    except urllib2.HTTPError,e:
        return 0
    i = re.search('count":(\d+)',html)

    if i is not None:
        no_of_tweets_raw = i.group(0)
    else:
        return 0
    
    j = re.search('(\d+)', no_of_tweets_raw)
    if j is not None:
        no_of_tweets = int(j.group())
    else:
        return 0

    return no_of_tweets




def socialsort(week):
    #for every article get shares
    for a in week:
        link=a.get_url()
        a.set_shares(facebook_likes(link)+twitter_likes(link))
    #sort by shares
    week.sort(key=lambda a:a._shares, reverse=True)
    sortedweek= week[0:int(len(week)/2+1)]
    sortedweek.sort(key=lambda a:a._ddate
       if (a and a._ddate)
       else datetime.date.today()
       )
    return sortedweek
