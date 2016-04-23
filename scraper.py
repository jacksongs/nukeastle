import scraperwiki
import requests
from bs4 import BeautifulSoup, CData
import pdfquery
import lxml
import datetime
# First, let's get the latest notifications. They arrive in a PDF every week, which is linked fro the below RSS.
rss = requests.get("http://www.newcastle.nsw.gov.au/Special-Pages/MediaFeed.aspx?rss=MediaFiles&directory=Documents&path=Development%20Applications/Weekly%20Notifications")
soup = BeautifulSoup(rss.content,"xml")
items = soup.rss.channel.find_all('item')

def rounddown(x, base=10):
    return int(base * round(float((x-5)/2)/base))
def roundup(x, base=10):
    return int(base * round(float((x+5)/2)/base))

data = []
for item in items[:1]:
	link = item.link.text
	# download the pdf...
	response = requests.get(link)
	with open('alerts.pdf', 'wb') as f:
		f.write(response.content)

	pdf = pdfquery.PDFQuery("alerts.pdf")
	crs = []
	for page in range(0,9999):
		try:
			# First, let's get the top and bottom of each row...
			# So let's find all the elements in the first column...
			pdf.load(page)
			rows = pdf.pq('LTTextLineHorizontal')

			rowlist = []
			for row in rows:
				rowlist.append([rounddown(float(row.get('y0'))),roundup(float(row.get('y1')))])

			for r in rowlist:
				boxes = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("%d, %d, %d, %d")'%(0,r[0],999,r[1]))
				if len(boxes) == 5: # So it it's a standard row, add it to the data
					cr = boxes[0].text.split(" ", 1)[0]
					add = boxes[0].text.split(" ", 1)[1] + boxes[1].text.title().strip() + " NSW"
					desc = boxes[2].text
					on_notice_from = boxes[4].text.split(" to ")[0] + " " + str(datetime.datetime.now().year)
					on_notice_to = boxes[4].text.split(" to ")[1]


					pass#print boxes.text().encode('utf-8')
					row = {"council_reference":    cr,
							"address":   add,
							"description":   desc,
							"info_url":   link,
							"comment_url":    "mailto:mail@ncc.nsw.gov.au?subject=Development+Application+Enquiry+"+cr,
							"date_scraped":    datetime.datetime.now().date().isoformat(),
							"on_notice_from":    on_notice_from.strip(),
							"on_notice_to":    on_notice_to
					}
					data.append(row)
		except Exception as e:
			print e
			break
			# No more pages

#print data
#print len(data) # target 68
scraperwiki.sqlite.save(unique_keys=['council_reference'], data=data)
