from main import Article,Scrape
import constants

s=Scrape(constants.Username,constants.Password)
Articlelist=s.query('sopa',location=constants.Geo,graph=False)
#use Articlelist[0].get_url  or get_title or get_desc or get_date
for a in Articlelist:
    a.printArticle()
    
    
