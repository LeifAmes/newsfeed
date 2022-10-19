#!/usr/bin/python3

import feedparser
import datetime, time
import time, datetime
import unicodedata
import re
import random
import json
import os, sys
import hashlib

articles_per_page = 12
num_pages = 5

script_path = "~/public_html/news"
base_path = os.path.join(script_path, "newsfeed-data")

feed_file = os.path.join(base_path, 'feeds.json')

article_file = os.path.join(base_path, 'articles.json')
article_data = []
if os.path.exists(article_file):
    article_data = json.loads(open(article_file, 'r', encoding="utf-8").read())

if not os.path.exists(base_path):
        os.makedirs(base_path)

def timestamp():
        return datetime.datetime.now().strftime("%Y%m%d-%H.%M.%S")

def read_timestamp(str):
        return datetime.datetime.strptime(str, ("%Y%m%d-%H.%M.%S"))


logfile = open(os.path.join(base_path, "newsbot.log"), 'w', encoding='utf-8')

def log(msg):
	print(repr(msg))
	logfile.write(timestamp() + ": " + msg + "\n")
	logfile.flush()

log("Newsbot starting")


def make_hash(msg):
        return hashlib.sha224(msg.encode('utf-8')).hexdigest()

# XXX  Move RSS feed config info to FILES
# RSS Feeds: Name, Site URL, RSS URL, Update frequency (seconds), Random interval (seconds)
rss_feeds = []

rss_feeds += [["Word", "http://wordsmith.org/words/today.html", "http://wordsmith.org/awad/rss1.xml", 4*60*60, 60*60]]
rss_feeds += [["Chinese Dictionary", "https://www.mdbg.net/chinese/dictionary?page=feeds", "https://www.mdbg.net/chinese/feed?feed=hsk", 1*60*60, 30*60]]
rss_feeds += [["OED", "https://www.oed.com/", "http://www.oed.com/rss/wordoftheday", 4*60*60, 60*60]]

rss_feeds += [["Stallman", "https://www.stallman.org/", "https://www.stallman.org/rss/rss.xml", 20*60, 20*60]]

rss_feeds += [["WIRED Top Stories", 'http://wired.com', "http://feeds.wired.com/wired/index", 20*60, 20*60]]
rss_feeds += [["WIRED Ideas", 'https://www.wired.com/category/ideas', "https://www.wired.com/feed/category/ideas/latest/rss", 20*60, 20*60]]
rss_feeds += [["WIRED Science", 'https://www.wired.com/category/science', "https://www.wired.com/feed/category/science/latest/rss", 20*60, 20*60]]
rss_feeds += [["WIRED Security", 'https://www.wired.com/category/security', "https://www.wired.com/feed/category/security/latest/rss", 20*60, 20*60]]

rss_feeds += [["Slashdot", 'https://slashdot.org', "https://rss.slashdot.org/Slashdot/slashdotMain", 20*60, 20*60]]

rss_feeds += [["HACKADAY", 'https://hackaday.com/blog/', "https://hackaday.com/blog/feed/", 20*60, 20*60]]
rss_feeds += [["Guardian USA", 'https://www.theguardian.com/us-news', "https://www.theguardian.com/us-news/rss", 20*60, 20*60]]
rss_feeds += [["Guardian Science", 'https://www.theguardian.com/science/', "https://www.theguardian.com/science/rss", 20*60, 20*60]]
rss_feeds += [["Guardian Tech", 'https://www.theguardian.com/technology', "https://www.theguardian.com/technology/rss", 20*60, 20*60]]


rss_next_check = [datetime.datetime.now() for i in range(len(rss_feeds))]
rss_last_seen = [["", ""] for i in range(len(rss_feeds))] # format: name, link


def dump_rss_feed(index):
	if index > len(rss_feeds):
		log("RSS feed out of range: index %s" % (index))

	log("Checking RSS Feed '%s'" % rss_feeds[index][0])

	(new_feed_articles, old_feed_articles, deleted_feed_articles) = (0, 0, 0)

	time_to_live = 60*60*48 # keep articles for 2 days after last seen

	url = rss_feeds[index][2]

	feed_filename = os.path.join(base_path, make_hash(url) + ".json")
	feed_data = {"articles":[], "last seen":[], "info":{}}
	if os.path.exists(feed_filename):
		feed_data = json.loads(open(feed_filename, 'r').read())
		log("Opened feed data for '%s'  %i articles read" % (rss_feeds[index][0], len(feed_data['articles'])))
	else:
		feed_data['info']['name'] = rss_feeds[index][0]
		feed_data['info']['url'] = rss_feeds[index][2]
		feed_data['info']['first checked'] = timestamp()
		log("Creating new feed file for '%s'" % rss_feeds[index][0])

	feed_data['info']['last checked'] = timestamp()


	feed = feedparser.parse(url)
	print("Processing:", rss_feeds[index])

	new_articles = []

	for item in feed['items']:
		title = item['title']
		summary = item['summary']
		url = item['links'][0]['href']
		author = ""
		if item.has_key('author'):
			author = item['author'].strip()

		article = [title, author, url]
		if article in feed_data['articles']:
			article_index = feed_data['articles'].index(article)
			feed_data['last seen'][article_index] = timestamp()
			old_feed_articles += 1

		else:
			# found a new article!
			feed_data['articles'].insert(0, article)
			feed_data['last seen'].insert(0, timestamp())
			new_articles += [article + [summary]]
			log("   New Article: '%s'" % title)
			new_feed_articles += 1

	for article in new_articles:
		title = article[0]
		article_data.insert(0, [rss_feeds[index][0], rss_feeds[index][1], title, article[2], article[3]])
		output = "%s %s :: %s <%s>" % (rss_feeds[index][0], title, article[3], article[2])
		print("\n\n", output, "\n\n")


    # Scan the article list for old articles to remove
	for i in reversed(range(len(feed_data['articles'])-1)): # count backwards so the index of earlier items remains consistent as we remove later items
		article_time = read_timestamp(feed_data['last seen'][i])
		if datetime.datetime.now() - article_time > datetime.timedelta(0, time_to_live, 0):
			article =  feed_data['articles'].pop(i)
			feed_data['last seen'].pop(i)
			log("   Article '%s' not seen for %s, removing..." % (article[0],  str(datetime.datetime.now() - article_time)))
			deleted_feed_articles += 1
                        
                
	# Done processing RSS feed, now write the feed state file
	open(feed_filename, 'w').write(json.dumps(feed_data))

	log("Finished checking '%s': %i new, %i old, %i deleted." % (rss_feeds[index][0], new_feed_articles, old_feed_articles, deleted_feed_articles))
	return new_feed_articles



def process_rss_feeds():
	new_articles = 0
	now = datetime.datetime.now()
	for index in range(len(rss_feeds)):
		if now > rss_next_check[index]:
			print("Processing RSS feed '%s'" % rss_feeds[index][0])
			rss_next_check[index] = datetime.datetime.now() + datetime.timedelta(0, rss_feeds[index][3] + random.random() * rss_feeds[index][4], 0)
			new_articles += dump_rss_feed(index)
			log("Next check for '%s': %s" % (rss_feeds[index][0], str(rss_next_check[index])))
	return new_articles



# Check the RSS feeds
new_articles = process_rss_feeds()

print("New articles:", new_articles)
if new_articles == 0:
    print("No update requied.")
    exit(0)



# Remove old articles
if len(article_data) > (articles_per_page * num_pages):
    article_data = article_data[:(articles_per_page * num_pages)]
 
# Write the article list
open(article_file, 'w', encoding="utf-8").write(json.dumps(article_data))

# Process the html output
for page in range(num_pages):
    if len(article_data) > page * articles_per_page:
        first_article = page * articles_per_page
        last_article = (page+1) * articles_per_page
        if last_article > len(article_data):
            last_article = len(article_data)
        page_name = "page%i.html" % (page+1)
        if page == 0:
            page_name = "index.html"
        last_source = article_data[first_article][0]
        side = 0
        page_file = open(os.path.join(script_path, page_name), "w", encoding="utf-8")
        page_file.write("".join(open(os.path.join(script_path, "header.txt"), "r").readlines()))
        
        for article_idx in range(first_article, last_article):
            if article_data[article_idx][0] != last_source:
                side ^= 1
                last_source = article_data[article_idx][0]
            if side == 0:
                page_file.write("""

<td>
  <table class="subpage">
    <tr>
      <td class="theader-ul"></td>
      <td class="theader-top"></td>
      <td rowspan=2 class="theader-ur"></td>
      <td rowspan=6 class="main-color" style="width: 7%;"></td>
      <td rowspan=6 class="main-right"></td>
    </tr>

    <tr>
      <td rowspan=2 class="theader-left"></td>
      <td rowspan=2 class="theader-color" style="font: 0.5cm Verdana, sans-serif; color: #00125f; text-align: right;">
<b><a href="{0}" target="_blank">{1}</a></b><br /><a href="{2}" target="_blank">{3}</a>
      </td>
    </tr><tr>
      <td class="theader-right" style="height: 1.5cm;"></td>
    </tr><tr>
      <td class="theader-ll"></td>
      <td class="theader-bottom"></td>
      <td class="theader-lr"></td>
    </tr><tr>
      <td class="tcontent-left"></td>
      <td class="tcontent-color" style="padding: 15px; padding-top: 3px; padding-bottom: 0px; font: 0.45cm Verdana, sans-serif; color: #00125f; text-align: justified;">
<p style="text-align: center;">{4}</p>
      </td>
      <td class="tcontent-right"></td>
      </tr><tr>
      <td class="tcontent-ll"></td>
      <td class="tcontent-bottom"></td>
      <td class="tcontent-lr"></td>
    </tr>
  </table>
</td></tr>
""".format(article_data[article_idx][1], article_data[article_idx][0], article_data[article_idx][3], article_data[article_idx][2], article_data[article_idx][4]))

            else:
                page_file.write("""
<tr><td>
  <table class="subpage">
    <tr>
      <td rowspan=6 class="main-left"></td>
      <td rowspan=6 class="main-color" style="width: 7%;"></td>
      <td rowspan=2 class="header-ul"></td>
      <td class="header-top"></td>
      <td class="header-ur"></td>
    </tr>
    <tr>
      <td rowspan=2 class="header-color" style="font: 0.5cm Verdana, sans-serif; color: #00125f;">
<b><a href="{0}" target="_blank">{1}</a></b><br /><a href="{2}" target="_blank">{3}</a>
      </td>
      <td rowspan=2 class="header-right"></td>
    </tr><tr>
      <td class="header-left" style="height: 1.5cm;"></td>
    </tr><tr>
      <td class="header-ll"></td>
      <td class="header-bottom"></td>
      <td class="header-lr"></td>
    </tr><tr>
      <td class="content-left"></td>
      <td class="content-color" style="padding: 15px; padding-top: 3px; padding-bottom: 0px; font: 0.45cm Verdana, sans-serif; color: #00125f; text-align: justified;">
<p style="text-align: center;">{4}</p>
      </td>
      <td class="content-right"></td>
      </tr><tr>
      <td class="content-ll"></td>
      <td class="content-bottom"></td>
      <td class="content-lr"></td>
    </tr>
  </table>
</td></tr>
""".format(article_data[article_idx][1], article_data[article_idx][0], article_data[article_idx][3], article_data[article_idx][2], article_data[article_idx][4]))

            if article_idx < last_article-1:
                page_file.write("""
<tr><td><table class="subpage">
  <tr>
    <td class="main-left"></td>
    <td class="main-color" style="height: 35px"></td>
    <td class="main-right"></td>
  </tr>
</table></td></tr>
""")
            else:
                nav_string=""
                if page == 0:
                    nav_string += '« prev :: 1 '
                else:
                    prev_page = "page%i.html" % (page)
                    if page == 1:
                        prev_page = "index.html"
                    nav_string += '<a href="%s">« prev </a>::<a href="index.html"> 1 </a>' % (prev_page)
                for i in range(1, num_pages):
                    if i == page:
                        nav_string += ':: %i ' % (i+1)
                    else:
                        nav_string += '::<a href="page%i.html"> %i </a>' % (i+1, i+1)
                if page == num_pages - 1:
                    nav_string += ':: next »'
                else:
                    nav_string += '::<a href="page%i.html"> next »</a>'% (page+2)
                page_file.write("""
<tr><td><table class="subpage">
  <tr>
    <td class="main-left"></td>
    <td class="main-color"><p style="text-align: center; font-weight: bold; color: #1065d5;">%s</p></td>
    <td class="main-right"></td>
  </tr>
</table></td></tr>
""" % (nav_string))           
        
        page_file.write("\n".join(open(os.path.join(script_path, "footer.txt"), "r").readlines()))
        page_file.close()
        
