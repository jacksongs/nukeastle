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


# Here a some rounding functions to help align lines on the pdf.
def rounddown(x, base=10):
    return int(base * round(float((x-5)/2)/base))
def roundup(x, base=10):
    return int(base * round(float((x+5)/2)/base))

# Now we just get the most recent alert pdfs. See the line two below this one.
data = []
for item in items[0:1]:
	link = item.link.text
	# Download the pdf...
	response = requests.get(link)
	with open('alerts.pdf', 'wb') as f:
		f.write(response.content)

	# Load the pdf into pdfquery...
	pdf = pdfquery.PDFQuery("alerts.pdf")
	crs = []
	for page in range(0,9999): # For each page (if it can't load the page, an error is caught. Hopefully there aren't any 10000 page docs!)
		try:
			# First, let's get the top and bottom of each row...
			# So let's find all the elements in the first column...
			pdf.load(page)
			rows = pdf.pq('LTTextLineHorizontal')
			print 'Page',page
			rowlist = set() # This will be a list of the rows, with the top and bottom y-values rounded up/down to 5.
			for row in rows:
				rowlist.update([int(float(row.get('y0')))])
			print 'Length of rowlist',len(rowlist)

			# Now let's check for each rowlist whether it has a council reference.
			rowlist2 = set()
			crlist = []
			for r in rowlist:
				boxes = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("%d, %d, %d, %d")'%(90,r,110,r+1))
				for b in boxes:
					if b.text[2]=='/':
						if b.text not in crlist:
							crlist.append(b.text)
							rowlist2.update([r])

			print 'Length of rowlist2',len(rowlist2)

			for r in rowlist2:
				boxes = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("%d, %d, %d, %d")'%(0,r,999,r+1))
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
				elif len(boxes) == 4: # This is pretty standard too
					for n in range(0,4):
						print n,boxes[n].text
				else:
					print boxes.text()
					print len(boxes)
		except Exception as e:
			print e
			break
			# No more pages

#print data
#print len(data),'(target 68)' # target 68
scraperwiki.sqlite.save(unique_keys=['council_reference'], data=data)
