#!/usr/bin/python
# encoding: utf-8
#
# Peteris Krumins (peter@catonmat.net)
# http://www.catonmat.net  --  good coders code, great reuse
#
# http://www.catonmat.net/blog/python-library-for-google-search/
#
# Code is licensed under MIT license.
#

import re
import urllib
from htmlentitydefs import name2codepoint
from BeautifulSoup import BeautifulSoup

from browser import Browser, BrowserError

class SearchError(Exception):
    """
    Base class for Google Search exceptions.
    """
    pass

class ParseError(SearchError):
    """
    Parse error in Google results.
    self.msg attribute contains explanation why parsing failed
    self.tag attribute contains BeautifulSoup object with the most relevant tag that failed to parse
    Thrown only in debug mode
    """
     
    def __init__(self, msg, tag):
        self.msg = msg
        self.tag = tag

    def __str__(self):
        return self.msg

    def html(self):
        return self.tag.prettify()

class SearchResult:
    def __init__(self, title, url, desc, date):
        self.title = title
        self.url = url
        self.desc = desc
        self.date = date
        
    def __str__(self):
        return 'Google Search Result: "%s"' % self.title

class GoogleSearch(object):
    SEARCH_URL_0 = "http://www.google.%(tld)s/search?hl=%(lang)s&gl=%(loc)s&tbs=cdr:1%%2Ccd_min%%3A%(monthstart)d%%2F%(daystart)d%%2F%(yearstart)d%%2Ccd_max%%3A%(monthend)d%%2F%(dayend)d%%2F%(yearend)d&tbm=nws&q=%(query)s"
    NEXT_PAGE_0 =  "http://www.google.%(tld)s/search?hl=%(lang)s&gl=%(loc)s&tbs=cdr:1%%2Ccd_min%%3A%(monthstart)d%%2F%(daystart)d%%2F%(yearstart)d%%2Ccd_max%%3A%(monthend)d%%2F%(dayend)d%%2F%(yearend)d&tbm=nws&q=%(query)s&start=%(start)d"
    SEARCH_URL_1 = "http://www.google.%(tld)s/search?hl=%(lang)s&gl=%(loc)s&tbs=cdr:1%%2Ccd_min%%3A%(monthstart)d%%2F%(daystart)d%%2F%(yearstart)d%%2Ccd_max%%3A%(monthend)d%%2F%(dayend)d%%2F%(yearend)d&tbm=nws&q=%(query)s&num=%(num)d"
    NEXT_PAGE_1 = "http://www.google.%(tld)s/search?hl=%(lang)s&gl=%(loc)s&tbs=cdr:1%%2Ccd_min%%3A%(monthstart)d%%2F%(daystart)d%%2F%(yearstart)d%%2Ccd_max%%3A%(monthend)d%%2F%(dayend)d%%2F%(yearend)d&tbm=nws&q=%(query)s&num=%(num)d&start=%(start)d"
    
    def __init__(self, query, random_agent=False, debug=False, lang="en", tld="com", re_search_strings=None,loc="us"):
        self.query = query
        self.debug = debug
        self.browser = Browser(debug=debug)
        self.results_info = None
        self.eor = False # end of results
        self._page = 0
        self._first_indexed_in_previous = None
        self._filetype = None
        self._last_search_url = None
        self._results_per_page = 10
        self._last_from = 0
        self._lang = lang
        self._tld = tld
        self._loc=loc
    
        if re_search_strings:
            self._re_search_strings = re_search_strings
        elif lang == "de":
            self._re_search_strings = ("Ergebnisse", "von", u"ungefähr")
        elif lang == "es":
            self._re_search_strings = ("Resultados", "de", "aproximadamente")
        # add more localised versions here
        else:
            self._re_search_strings = ("Results", "of", "about")

        if random_agent:
            self.browser.set_random_user_agent()

    @property
    def num_results(self):
        if not self.results_info:
            page = self._get_results_page()
            self.results_info = self._extract_info(page)
            if self.results_info['total'] == 0:
                self.eor = True
        return self.results_info['total']

    @property
    def last_search_url(self):
        return self._last_search_url

    def _get_page(self):
        return self._page

    def _set_page(self, page):
        self._page = page

    page = property(_get_page, _set_page)

    def _set_start_date(self,month,day,year):
        self._monthstart=month
        self._daystart=day
        self._yearstart=year

    def _set_end_date(self,month,day,year):
        self._monthend=month
        self._dayend=day
        self._yearend=year
    
    def _get_first_indexed_in_previous(self):
        return self._first_indexed_in_previous

    def _set_first_indexed_in_previous(self, interval):
        if interval == "day":
            self._first_indexed_in_previous = 'd'
        elif interval == "week":
            self._first_indexed_in_previous = 'w'
        elif interval == "month":
            self._first_indexed_in_previous = 'm'
        elif interval == "year":
            self._first_indexed_in_previous = 'y'
        else:
            # a floating point value is a number of months
            try:
                num = float(interval)
            except ValueError:
                raise SearchError, "Wrong parameter to first_indexed_in_previous: %s" % (str(interval))
            self._first_indexed_in_previous = 'm' + str(interval)
    
    first_indexed_in_previous = property(_get_first_indexed_in_previous, _set_first_indexed_in_previous, doc="possible values: day, week, month, year, or a float value of months")
    
    def _get_filetype(self):
        return self._filetype

    def _set_filetype(self, filetype):
        self._filetype = filetype
    
    filetype = property(_get_filetype, _set_filetype, doc="file extension to search for")
    
    def _get_results_per_page(self):
        return self._results_per_page

    def _set_results_par_page(self, rpp):
        self._results_per_page = rpp

    results_per_page = property(_get_results_per_page, _set_results_par_page)

    def get_results(self):
        """ Gets a page of results """
        if self.eor:
            return []
        MAX_VALUE = 1000000
        page = self._get_results_page()
        #search_info = self._extract_info(page)
        results = self._extract_results(page)
        #print 'results', results
        search_info = {'from': self.results_per_page*self._page,
                       'to': self.results_per_page*self._page + len(results),
                       'total': MAX_VALUE}
        if not self.results_info:
            self.results_info = search_info
            if self.num_results == 0:
                self.eor = True
                return []
        if not results:
            self.eor = True
            return []
        if self._page > 0 and search_info['from'] == self._last_from:
            self.eor = True
            return []
        if search_info['to'] == search_info['total']:
            self.eor = True
        self._page += 1
        self._last_from = search_info['from']
        return results

    def _maybe_raise(self, cls, *arg):
        if self.debug:
            raise cls(*arg)

    def _get_results_page(self):
        if self._page == 0:
            if self._results_per_page == 10:
                print  'search_url_0'
                url = GoogleSearch.SEARCH_URL_0
            else:
                print  'search_url_1'
                url = GoogleSearch.SEARCH_URL_1
        else:
            if self._results_per_page == 10:
                print  'next_page_0'
                url = GoogleSearch.NEXT_PAGE_0
            else:
                print  'next_page_1'
                url = GoogleSearch.NEXT_PAGE_1
        
        #print url
        
        safe_url = [url % { 'query': urllib.quote_plus(self.query),
                           'start': self._page * self._results_per_page,
                           'num': self._results_per_page,
                           'tld' : self._tld,
                           'lang' : self._lang,
                            'loc' : self._loc,
                            'monthstart' : self._monthstart,
                            'daystart' : self._daystart,
                            'yearstart' : self._yearstart,
                            'monthend' : self._monthend,
                            'dayend' : self._dayend,
                            'yearend' : self._yearend}]
        #print safe_url
        # possibly extend url with optional properties
        if self._first_indexed_in_previous:
            safe_url.extend(["&as_qdr=", self._first_indexed_in_previous])
        if self._filetype:
            safe_url.extend(["&as_filetype=", self._filetype])
        
        safe_url = "".join(safe_url)
        self._last_search_url = safe_url
        
        try:
            page = self.browser.get_page(safe_url)
            
        except BrowserError, e:
            raise SearchError, "Failed getting %s: %s" % (e.url, e.error)

        return BeautifulSoup(page)

    def _extract_info(self, soup):
        empty_info = {'from': 0, 'to': 0, 'total': 0}
        div_ssb = soup.find('div', id='ssb')
        if not div_ssb:
            self._maybe_raise(ParseError, "Div with number of results was not found on Google search page", soup)
            return empty_info
        p = div_ssb.find('p')
        if not p:
            self._maybe_raise(ParseError, """<p> tag within <div id="ssb"> was not found on Google search page""", soup)
            return empty_info
        txt = ''.join(p.findAll(text=True))
        txt = txt.replace(',', '')
        matches = re.search(r'%s (\d+) - (\d+) %s (?:%s )?(\d+)' % self._re_search_strings, txt, re.U)
        if not matches:
            return empty_info
        return {'from': int(matches.group(1)), 'to': int(matches.group(2)), 'total': int(matches.group(3))}

    def _extract_results(self, soup):
        results = soup.findAll('li', {'class': 'g'})
        #results = soup.findAll('li', 'g')
        ret_res = []
        for result in results:
            #print 'single result',result
            eres = self._extract_result(result)
            #print 'eres',eres
            if eres:
                ret_res.append(eres)
        return ret_res

    def _extract_result(self, result):
        title, url = self._extract_title_url(result)
        desc = self._extract_description(result)
        date = self._extract_date(result)
        #print 'title',title
        #print 'url',url
        #print 'desc',desc
        if not title or not url or not desc:
            return None
        return SearchResult(title, url, desc,date)

    def _extract_title_url(self, result):
        title_a = result.find('a', {'class': re.compile(r'\bl\b')})
        #print 'title_a',title_a
        #title_a = result.find('a')
        if not title_a:
            #print' hit error'
            self._maybe_raise(ParseError, "Title tag in Google search result was not found", result)
            return None, None
        title = ''.join(title_a.findAll(text=True))
        #print 'title',title
        title = self._html_unescape(title)
        #print 'title2',title
        url = title_a['href']
        #print 'url',url
        match = re.match(r'/url\?q=(http[^&]+)&', url)
        if match:
            url = urllib.unquote(match.group(1))
            #print 'url2',url
        return title, url
    
    def _extract_date(self,result):
        desc_div = result.findAll('span','f nsa')
        if not desc_div:
            self._maybe_raise(ParseError, "Description tag in Google search result was not found", result)
            return None
        #print 'date', desc_div
        for d in desc_div:
            match=re.match(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d\d*,\s\d{4}',d.renderContents())
            if match:
                #print match
                #print match.group()
                break
        return match.group()
        
        
    def _extract_description(self, result):
        #desc_div = result.find('div', {'class': re.compile(r'\bst\b')})
        desc_div = result.find('span','st')
        if not desc_div:
            desc_div = result.find('div', {'class': re.compile(r'\bst\b')})    
        if not desc_div:
            self._maybe_raise(ParseError, "Description tag in Google search result was not found", result)
            return None

        desc_strs = []
        def looper(tag):
            if not tag: return
            for t in tag:
                try:
                    if t.name == 'br': break
                except AttributeError:
                    pass

                try:
                    desc_strs.append(t.string)
                except AttributeError:
                    desc_strs.append(t)

        looper(desc_div)
        looper(desc_div.find('wbr')) # BeautifulSoup does not self-close <wbr>

        desc = ''.join(s for s in desc_strs if s)
        return self._html_unescape(desc)

    def _html_unescape(self, str):
        def entity_replacer(m):
            entity = m.group(1)
            if entity in name2codepoint:
                return unichr(name2codepoint[entity])
            else:
                return m.group(0)

        def ascii_replacer(m):
            cp = int(m.group(1))
            if cp <= 255:
                return unichr(cp)
            else:
                return m.group(0)

        s =    re.sub(r'&#(\d+);',  ascii_replacer, str, re.U)
        return re.sub(r'&([^;]+);', entity_replacer, s, re.U)

class BlogSearch(GoogleSearch):

    def _extract_info(self, soup):
        empty_info = {'from': 0, 'to': 0, 'total': 0}
        td_rsb = soup.find('td', 'rsb')
        if not td_rsb:
            self._maybe_raise(ParseError, "Td with number of results was not found on Blogs search page", soup)
            return empty_info
        font = td_rsb.find('font')
        if not font:
            self._maybe_raise(ParseError, """<p> tag within <tr class='rsb'> was not found on Blogs search page""", soup)
            return empty_info
        txt = ''.join(font.findAll(text=True))
        txt = txt.replace(',', '')
        if self.hl == 'es':
            matches = re.search(r'Resultados (\d+) - (\d+) de (?:aproximadamente )?(\d+)', txt, re.U)
        elif self.hl == 'en':
            matches = re.search(r'Results (\d+) - (\d+) of (?:about )?(\d+)', txt, re.U)
        if not matches:
            return empty_info
        return {'from': int(matches.group(1)), 'to': int(matches.group(2)), 'total': int(matches.group(3))}

    def _extract_results(self, soup):
        results = soup.findAll('p', {'class': 'g'})
        ret_res = []
        for result in results:
            eres = self._extract_result(result)
            if eres:
                ret_res.append(eres)
        return ret_res

    def _extract_result(self, result):
        title, url = self._extract_title_url(result)
        desc = self._extract_description(result)
        if not title or not url or not desc:
            return None
        return SearchResult(title, url, desc)

    def _extract_title_url(self, result):
        #title_a = result.find('a', {'class': re.compile(r'\bl\b')})
        title_a = result.findNext('a')
        if not title_a:
            self._maybe_raise(ParseError, "Title tag in Blog search result was not found", result)
            return None, None
        title = ''.join(title_a.findAll(text=True))
        title = self._html_unescape(title)
        url = title_a['href']
        match = re.match(r'/url\?q=(http[^&]+)&', url)
        if match:
            url = urllib.unquote(match.group(1))
        return title, url

    def _extract_description(self, result):
        desc_td = result.findNext('td')
        if not desc_td:
            self._maybe_raise(ParseError, "Description tag in Google search result was not found", result)
            return None

        desc_strs = []
        def looper(tag):
            if not tag: return
            for t in tag:
                try:
                    if t.name == 'br': break
                except AttributeError:
                    pass

                try:
                    desc_strs.append(t.string)
                except AttributeError:
                    desc_strs.append(t)

        looper(desc_td)
        looper(desc_td.find('wbr')) # BeautifulSoup does not self-close <wbr>

        desc = ''.join(s for s in desc_strs if s)
        return self._html_unescape(desc)
        
