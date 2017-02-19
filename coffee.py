# -*- coding: utf-8 -*-
#
# Caffeinate Me! - CoffeeReviews.com Website Scraper
#
#
# ---------- Start of User Configurable Variables ------------- #
username = ''
password = ''
debug = True
outfile = 'coffee.csv'
no_of_pages = int(225) # Number of search pages to process
ntd_hkd_rate = float(0.25)
rmb_hkd_rate = float(1.13)
ounce_to_grams = float(28.3495 )
pound_to_grams = float(453.592)
kilogram_to_grams = float(1000)
# ---------- End of User Configurable Variables --------------- #

# Imports
import mechanize
import cookielib
from bs4 import BeautifulSoup
import csv
from currency_converter import CurrencyConverter
import sys
from datetime import datetime
import signal
import traceback

# Catch Control-C
def signal_handler(signal, frame):
   end_time = datetime.now()
   print "\n" + str(count) + " coffees processed in " + str(end_time - start_time) + " seconds\n"
   sys.exit(0)

# Set codepage
reload(sys)  
sys.setdefaultencoding('utf8')

# Start timing
start_time = datetime.now()

# Catch Control-C, flush buffer to CSV
signal.signal(signal.SIGINT, signal_handler)

# URLs
base_url = 'http://www.coffeereview.com'
search_url = base_url + '/advanced-search/?pg='
login_url = base_url + '/login/'
count = 0
errors = []

# CurrencyConverter
c = CurrencyConverter()

# Browser
br = mechanize.Browser()

# Cookie Jar
cj = cookielib.LWPCookieJar()
br.set_cookiejar(cj)

# Browser options
br.set_handle_equiv(True)
br.set_handle_gzip(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_robots(False)

# Follows refresh 0 but not hangs on refresh > 0
br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

# Want HTTP debug messages?
#br.set_debug_http(True)
#br.set_debug_redirects(True)
#br.set_debug_responses(True)

# User-Agent, not!
br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

# Open the login page
r = br.open(login_url)

# Select Login Form
br.select_form(nr=1)
br.form['log'] = username
br.form['pwd'] = password
br.submit()

# Woohoo! We're in! Now Open / Overwrite a (new/old) CSV file
with open(outfile, 'w') as csvfile:

   fieldnames = [
    'company', 'coffee', 'geisha', 'score', 'location',
    'origin', 'roast', 'price_text', 'price', 'currency', 'weight', 'weight_unit', 
    'weight_grams', 'hkd', 'date', 'agtron', 'aroma', 'acidity', 'body',
    'flavour', 'aftertaste', 'url', 'blind_assessment', 'notes', 'bottom_line'
   ]
   writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
   writer.writeheader()

   for page in range(1, no_of_pages):
   
      if debug:
         print "=============== Processing page " + str(page) + " =================="

      # Get Search Pages One at a Time
      r = br.open(search_url + str(page))
      soup = BeautifulSoup(r.read(), 'html.parser')
      links = soup.find_all('div', attrs={'class':'links'})

      for x in range(0, len(links)):
         count = count + 1
        
         this_coffee = {
            'company': '',  'coffee': '', 'score': '', 'location': '',
            'origin': '', 'roast': '', 'price': '', 'date': '',
            'agtron': '', 'aroma': '', 'acidity': '', 'body': '',
            'flavour': '', 'aftertaste': '', 'currency': '', 'weight': '', 
            'hkd': '', 'weight_unit': '', 'weight_grams': '', 'blind_assessment': '',
            'notes': '', 'bottom_line': '', 'price_text': '', 'geisha': ''
         }
      
         review = base_url + links[x].find('a').get('href')
         
         if debug:
            # Something to stare at...
            print "Processing: " + review + " (" + str(count) + ")"
         
         r = br.open(review)
         soup = BeautifulSoup(r.read(), 'html.parser')

         col1 = soup.find("div", { "class" : "review-col1"})
         col2 = soup.find("div", { "class" : "review-col2"})
         
         # Yuck!
         try:
            this_coffee['score'] = col1.find('div', attrs={ 'class': 'review-rating'} ).text.strip()
            this_coffee['company'] = col1.find('h3').text.strip()
            this_coffee['coffee'] = col1.find('h2', attrs={ 'class': 'review-title'} ).text.strip()
            
            if this_coffee['coffee'].find('Geisha') != -1:
               this_coffee['geisha'] = 'Yes'
            else:
               this_coffee['geisha'] = 'No'
            
            this_coffee['location'] = col1.find_all('strong')[0].text.strip()
            this_coffee['origin'] = col1.find_all('strong')[1].text.strip()
            this_coffee['roast'] = col1.find_all('strong')[2].text.strip()
            
            
            try:
               this_coffee['price_text'] = col1.find_all('strong')[3].text.strip()

               # Seperate dollars, pounds and euros
               if this_coffee['price_text'].find('$') != -1:
                  this_coffee['price'] = this_coffee['price_text'].split('$')[1].strip().split('/')[0].strip().replace(',', '')
                  this_coffee['currency'] = this_coffee['price_text'].split('$')[0].strip()
               elif this_coffee['price_text'].find('£') != -1:
                  this_coffee['price'] = this_coffee['price_text'].split('£')[1].strip().split('/')[0].strip().replace(',', '')
                  this_coffee['currency'] = 'UKP'
               elif this_coffee['price_text'].find('€') != -1:
                  this_coffee['price'] = this_coffee['price_text'].split('€')[1].strip().split('/')[0].strip().replace(',', '')
                  this_coffee['currency'] = 'EUR'
                  
               
               this_coffee['weight'] = col1.find_all('strong')[3].text.split('$')[1].strip().split('/')[1].strip().split(" ")[0]
               this_coffee['weight_unit'] = col1.find_all('strong')[3].text.split('$')[1].strip().split('/')[1].strip().split(" ")[1]
               
               if this_coffee['weight_unit'] == 'ounces' or this_coffee['weight_unit'] == 'ounces.':
                  this_coffee['weight_grams'] = float(this_coffee['weight']) * ounce_to_grams
               elif this_coffee['weight_unit'] == 'oz.':
                  this_coffee['weight_grams'] = float(this_coffee['weight']) * ounce_to_grams
               elif this_coffee['weight_unit'] == 'pound':
                  this_coffee['weight_grams'] = float(this_coffee['weight']) * pound_to_grams
               elif this_coffee['weight_unit'] == 'grams':
                  this_coffee['weight_grams'] = float(this_coffee['weight'])
               elif this_coffee['weight_unit'] == 'g.':
                  this_coffee['weight_unit'] = 'grams'
                  this_coffee['weight_grams'] = this_coffee['weight_unit']
               elif this_coffee['weight_unit'] == 'kilogram':
                  this_coffee['weight_grams'] = float(this_coffee['weight']) * kilogram_to_grams
               elif this_coffee['weight_unit'] == 'kg.':
                  this_coffee['weight_unit'] = 'kilogram'
                  this_coffee['weight_grams'] = float(this_coffee['weight']) * kilogram_to_grams

                  
               # Assume USD if no currency listed
               if this_coffee['currency'] == '':
                  this_coffee['currency'] = 'USD'
               elif this_coffee['currency'] == 'US':
                  this_coffee['currency'] = 'USD'
               elif this_coffee['currency'] == 'HK':
                  this_coffee['currency'] = 'HKD'
                  
               # Convert to HKD
               if this_coffee['currency'] == 'NT':
                  # NT is not supported by currenct converter
                  this_coffee['hkd'] = float(this_coffee['price']) * ntd_hkd_rate
               elif this_coffee['currency'] == 'RMB':
                  # Neither is RMB
                  this_coffee['hkd'] = float(this_coffee['price']) * rmb_hkd_rate
               elif this_coffee['currency'] == 'NTD':
                  # Neither is NTD
                  this_coffee['hkd'] = float(this_coffee['price']) * ntd_hkd_rate
               elif this_coffee['currency'] == 'TWD':
                  # Neither is NTD
                  this_coffee['hkd'] = float(this_coffee['price']) * ntd_hkd_rate
               else:
                  this_coffee['hkd'] = c.convert(this_coffee['price'], this_coffee['currency'], 'HKD')
                  
            except Exception as e: 
               if debug:
                  print str(e)
                  traceback.print_exc()
               
               this_coffee['price'] = ''
               this_coffee['currency'] = ''
               this_coffee['weight'] = ''
               
            this_coffee['date'] = location = col2.find_all('strong')[0].text.strip()
            this_coffee['agtron'] = location = col2.find_all('strong')[1].text.strip()
            this_coffee['aroma'] = location = col2.find_all('strong')[2].text.strip()
            this_coffee['acidity'] = location = col2.find_all('strong')[3].text.strip()
            this_coffee['body'] = col2.find_all('strong')[4].text.strip()
            this_coffee['flavour'] = col2.find_all('strong')[5].text.strip()
            this_coffee['aftertaste'] = col2.find_all('strong')[6].text.strip()
            this_coffee['url'] = review.strip()
            
            this_coffee['blind_assessment'] = soup.find_all("p", { "class" : "subtitle"})[0].nextSibling.nextSibling.text.strip()
            this_coffee['notes'] = soup.find_all("p", { "class" : "subtitle"})[1].nextSibling.nextSibling.text.strip()
            this_coffee['bottom_line'] = soup.find_all("p", { "class" : "subtitle"})[1].nextSibling.nextSibling.nextSibling.nextSibling.text.strip()
            
         except Exception as e:
            # Meh...
            print "Error parsing page: " + review
            print "---------- DEBUG ------------"
            print str(e)
            traceback.print_exc()
            print "-----------------------------"
            
            errors.append(review)
            
            continue

         # Write the Dictionary to CSV
         try:
            writer.writerow(this_coffee)
         except:
            # Whatever...
            continue
   
   if len(errors) != 0:
      print "The following coffee reviews had errors and were not included in the dump file:"
      for y in range(0, len(errors)):
         print errors[y]
