from django.shortcuts import render_to_response
from django.http import HttpResponse
from followthestory.Gcode.main import Article,Scrape
import followthestory.Gcode.constants as constants
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import datetime
import Gcode.pruning as pruning
import Gcode.twitter_main as twitterfeed


def search_form(request):
    return render_to_response('search_form.html')

def search(request):
    if 'q' in request.GET:
        q=request.GET['q']
        s=Scrape(constants.Username,constants.Password)
        Articlelist=s.query(q,location=constants.Geo,graph=True)
        ##pruning
        Articlelist=sorted(Articlelist, key=lambda a:a._ddate
           if (a and a._ddate)
           else datetime.date.today()
           )
        sortedweek=list()
        startd=Articlelist[0].get_ddate()
        endd=startd+datetime.timedelta(days=7)
        while startd<=Articlelist[-1].get_ddate() :
            #get artciles between startdate and enddate
            week=[art for art in Articlelist if (art.get_ddate() >=startd and art.get_ddate()<endd)]
            #pass them to socialsort
            sortedweek+=pruning.socialsort(week)
            # update dates
            startd=endd
            endd=startd+datetime.timedelta(days=7)
    
        articledictlist=list()
        dic={}
        for a in sortedweek:
            dic['url']=a.get_url()
            dic['title']=a.get_title()
            dic['desc']=a.get_desc()
            dic['date']=a.get_date()
            articledictlist.append(dic.copy())
            
        Total=len(Articlelist)
        #-------get twitter feed--------#
        tquery=q.replace(' ',' OR #')
        tquery="#"+tquery        
        tobj=twitterfeed.TagCrawler(None,tquery,None)
        tfeed=list()
        for i in range(1,constants.twitterpages+1):
            tfeed+=tobj.search(page=i)
            print i
        tfeedtext=list()
        for i in range (0,len(tfeed)):
            tfeedtext.append(tfeed[i]['text'])
        positive,negative,neutral=tobj.classify(tfeedtext)    
        return render_to_response('search_results.html',{'articledictlist':articledictlist,'query':q,'Total':Total,'positive':positive,'negative':negative,'neutral':neutral,'twitterfeed':tfeedtext,'tquery':tquery})
    else:
        message = 'You submitted empty.'
        return HttpResponse(message)

def plot_graph(request):
    imagePath=constants.graphfile
    from PIL import Image
    Image.init()
    i=Image.open(imagePath)

    response=HttpResponse(mimetype='image/png')
    i.save(response,'PNG')
    return response

def plot_twittergraph(request):
    imagePath=constants.twittergraphfile
    from PIL import Image
    Image.init()
    i=Image.open(imagePath)

    response=HttpResponse(mimetype='image/png')
    i.save(response,'PNG')
    return response
