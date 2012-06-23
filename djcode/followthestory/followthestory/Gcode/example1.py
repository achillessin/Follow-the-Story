#!/usr/bin/python
#
# This program does a Google search for "quick and dirty" and returns
# 50 results.
#

from xgoogle.search import GoogleSearch, SearchError
try:
  gs = GoogleSearch("sopa")
  gs._results_per_page = 10 #(default,dont change)
  print 'setting dates'
  gs._set_start_date(month=4,day=1,year=2012)
  gs._set_end_date(month=4,day=12,year=2012)
  #gs._set_page(page=2)
  print 'getting results'
  results = gs.get_results()
  for res in results:
    print res.title.encode('utf8')
    print res.desc.encode('utf8')
    print res.url.encode('utf8')
    print
except SearchError, e:
  print "Search failed: %s" % e

#span class="f nsa"
#re.findall(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d\d*,\s\d{4}',i)
