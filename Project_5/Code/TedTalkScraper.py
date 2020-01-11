from __future__ import print_function, division
import requests
import csv
import pandas as pd
from collections import defaultdict
from bs4 import BeautifulSoup
import time
import re
import numpy as np
import pickle as pkl
from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

import os
chromedriver = "/Applications/chromedriver" # path to the chromedriver executable
os.environ["webdriver.chrome.driver"] = chromedriver

requests.__path__


#Collect Links of all videos
def scrapelinks():
    """
    Scraping the links of all individual videos
    """
    links = []
    broken = []
    count = 0
    for page in range(1,113):
        url = 'https://www.ted.com/talks?page='+str(page)
        response = requests.get(url)
        soup = BeautifulSoup(response.text,'lxml')
        x = soup.find_all('a',class_ = 'ga-link', attrs = {'data-ga-context':'talks'})
        if len(x) == 0:
            broken.append(page)
        else:
            for i in range(0,len(x),2):
                count += 1
                links.append(x[i]['href'])
    return links, broken


def scrapebrokenpages(links, pages):
    """
    Returns the complete list of Ted video links. The website realizes that a
    bot is scraping the information and hence locks the bot out sometimes.
    That is reflected in the brokenpages. The website is scraped until no brokenpages exist anymore.
    """
    link = links
    broken = []
    for page in pages:
        url = 'https://www.ted.com/talks?page='+str(page)
        response = requests.get(url)
        soup = BeautifulSoup(response.text,'lxml')
        x = soup.find_all('a',class_ = 'ga-link', attrs = {'data-ga-context':'talks'})
        if len(x) == 0:
            broken.append(page)
        for i in range(0,len(x),2):
            link.append(x[i]['href'])
    if broken != []:
        scrapebrokenpages(link, broken)
    return link

#Formulas for scraping video information
def getviews(soup):
    """
    Scraping the number of views
    """
    try:
        number = soup.find('div', class_ = 'd:i-b f-w:700 f:.9 f:1@xxl').text
        number_list = re.findall(r'\d+',number)
        if number.find(',') == -1:
            numbers = number_list[0]
        elif number.count(',') == 1:
            numbers = ''.join(number_list[0:2])
        else:
            numbers = ''.join(number_list[0:3])
    except:
        numbers = np.NaN
    return numbers


def getlength(soup):
    """
    Scraping the length of the video
    """
    try:
        number = soup.find('div', class_ = 'd:i-b f-w:700 f:.9 f:1@xxl').text
        number_list = list(map(int,re.findall(r'\d+',number)))
        if number.find(':') == -1:
            numbers = number_list[-1]
        elif number.count(':') == 1:
            numbers = np.sum(number_list[-2])*60+number_list[-1]
        else:
            numbers = np.sum(number_list[-3])*(60**2)+np.sum(number_list[-2])*60+number_list[-1]
    except:
        numbers = np.NaN
    return numbers


def getdescription(soup):
    """
    Scraping the description of TED videos
    """
    try:
        z = str(soup.find('meta', attrs = {'name':'description'}))
        index1 = z.index('"')
        index2 = z.index('"', index1+1)
        description = z[index1+1:index2]
    except:
        description = np.NaN

    return description


def getauthor(soup):
    """
    Scraping the author of the talk
    """
    try:
        z = str(soup.find('meta', attrs = {'name':'author'}))
        index1 = z.index('"')
        index2 = z.index('"', index1+1)
        author = z[index1+1:index2]
    except:
        author = np.NaN
    return author


def getkeywords(soup):
    """
    Scraping the keywords describing the video
    """
    try:
        z = str(soup.find('meta', attrs = {'name':'keywords'}))
        index1 = z.find('"')
        index2 = z.find('"', index1+1)
        keywords = z[index1+1:index2]
        keywords = keywords.split(',')
    except:
        keywords = np.NaN
    return keywords


def getupload(soup):
    """
    Scraping the upload date of the video
    """
    z = str(soup.find('meta', attrs = {'itemprop':'uploadDate'}))
    index1 = z.find('"')
    index2 = z.find('"', index1+1)
    date = z[index1+1:index2]
    return date


def getevent(soup):
    """
    Scraping the name of the event
    """
    try:
        h = str(soup.find_all('script', attrs = {'data-spec':"q"}))
        start = h.find('event')
        intermediate = h.find(":", start+1)
        stop = h.find('"',intermediate+2)
        event = h[intermediate+2:stop]
    except:
        event = np.NaN
    return event


def getjob(soup):
    """
    Scraping the profession of the author
    """
    try:
        job = soup.find('span',  class_ = 'd:b d:i@md c:gray-d f:.9' ).text
    except:
        job = np.NaN
    return job


def getyear(soup):
    """
    Scraping the year of the talk
    """
    try:
        h = str(soup.find_all('script', attrs = {'data-spec':"q"}))
        start = h.find('author')
        intermediate = h.find('"year"', start)
        stop = h.find(':',intermediate+2)
        final = h.find('"',stop+2)
        year = h[stop+2:final]
    except:
        year = np.NaN
    return year


def getspeakerdescription(soup):
    """
    Scraping the description of the speaker
    """
    try:
        h = str(soup.find_all('script', attrs = {'data-spec':"q"}))
        start = h.find('whotheyare')
        stop = h.find(':',start)
        final = h.find('"',stop+2)
        desc =h[stop+2:final]
    except:
        desc = np.NaN
    return desc


def getratings(soup):
    """
    Scraping the ratings of the talk
    """
    try:
        h = str(soup.find_all('script', attrs = {'data-spec':"q"}))
        start = h.find('ratings')
        intermediate = h.find("[", start)
        stop = h.find(']',intermediate+1)
        ratings = h[intermediate:stop+1].split(',')
        d_list = []
        for k in range(len(ratings)//3):
            d = defaultdict(int)
            if k == 0:
                rating = ratings[0:3]
            else:
                rating = ratings[(k*3):(k*3+3)]
            for i in rating:
                start = i.find('"')+1
                stop = i.find('"',start)
                if i[start:stop] == 'name':
                    start1 = i.find(':',stop)+2
                    stop1 = i.find('"',start1)
                    d[i[start:stop]] = i[start1:stop1]
                else:
                    start1 = re.findall(r'\d+', i)
                    d[i[start:stop]] = int(start1[0])
            d_list.append(d)
    except:
        d_list = np.NaN
    return d_list


def getlanguages(soup):
    """
    Scraping the number of languages the transcripts are available
    """
    try:
        result = soup.find_all('span',class_ = "css-i4xfca")[1].get_text()
        number = int(re.findall('\d+', result)[0])
    except:
        number = np.NaN
    return number


def gettitle(soup):
    """
    Scraping the title of the video
    """
    try:
        z = str(soup.find('meta', attrs = {'name':'title'}))
        index1 = z.find(':')
        index2 = z.find('name=', index1)
        title = z[index1+1:index2-2].strip()
    except:
        title = np.NaN
    return title


def getcommentsnumber(soup):
    """
    Scraping the number of comments
    """
    try:
        s = re.compile('Comments')
        comments = soup.find(text=s)
        number = int(re.findall('\d+', comments)[0])
    except:
        number = np.NaN
    return number


def geteventdate(soup):
    """
    Scraping the month and year of the event
    """
    try:
        string = soup.find_all('span', class_ = 'f-w:700')[2].findNextSibling().text
        start = string.find(' ')
        date = string[start+1:]
    except:
        date = np.NaN
    return date


#Function which calls formulas to collect video informations
def scrapeinfo(weblinks1, count1):
    driver = webdriver.Chrome(chromedriver)
    teddict = defaultdict(str)
    title = []
    views = []
    videolength = []
    videodescription = []
    author = []
    keywords = []
    event = []
    upload = []
    authorjob = []
    year = []
    speakerdescription = []
    rating = []
    languages = []
    comments = []
    eventdate = []
    count = count1
    weblinks = weblinks1[count1:]
    for link in weblinks:
        count += 1
        url = 'https://www.ted.com'+link
        driver.get(url)
        soup = BeautifulSoup(driver.page_source,'lxml')
        #Scrape Title
        title.append(gettitle(soup))
        #Scrape views
        views.append(getviews(soup))
        #Scrape videolength
        videolength.append(getlength(soup))
        #video description
        videodescription.append(getdescription(soup))
        #author
        author.append(getauthor(soup))
        #Keywords
        keywords.append(getkeywords(soup))
        #Event
        event.append(getevent(soup))
        #Upload
        upload.append(getupload(soup))
        #Job
        authorjob.append(getjob(soup))
        #Year
        year.append(getyear(soup))
        #Speaker Description
        speakerdescription.append(getspeakerdescription(soup))
        #Ratings
        rating.append(getratings(soup))
        #Number of languages
        languages.append(getlanguages(soup))
        #Number of Comments
        comments.append(getcommentsnumber(soup))
        #Event data
        eventdate.append(geteventdate(soup))
        print(count)
        if count % 500 == 0:
            teddict['Title'] = title
            teddict['Views'] = views
            teddict['Length'] = videolength
            teddict['Description'] = videodescription
            teddict['Author'] = author
            teddict['Keywords'] = keywords
            teddict['Event'] = event
            teddict['Upload Date'] = upload
            teddict['Profession'] = authorjob
            teddict['Year'] = year
            teddict['Speaker Description'] = speakerdescription
            teddict['Rating'] = rating
            teddict['Languages'] = languages
            teddict['Comments'] = comments
            teddict['Event Date'] = eventdate
            teddict['Links'] = links[count1:count]
            print('Title:'+str(len(teddict['Title'])))
            print('Views:'+str(len(teddict['Views'])))
            print('Length:'+str(len(teddict['Length'])))
            print('Description:'+str(len(teddict['Description'])))
            print('Author:'+str(len(teddict['Author'])))
            print('Keywords:'+str(len(teddict['Keywords'])))
            print('Event:'+str(len(teddict['Event'])))
            print('Upload Date:'+str(len(teddict['Upload Date'])))
            print('Profession:'+str(len(teddict['Profession'])))
            print('Year:'+str(len(teddict['Year'])))
            print('Speaker Description:'+str(len(teddict['Speaker Description'])))
            print('Rating:'+str(len(teddict['Rating'])))
            print('Languages:'+str(len(teddict['Languages'])))
            print('Comments:'+str(len(teddict['Comments'])))
            print('Event Date:'+str(len(teddict['Event Date'])))
            print('Links:'+str(len(teddict['Links'])))
            df = pd.DataFrame(teddict)
            pkl.dump(df,open('/Users/ferdinandwohlenberg/Desktop/Projects/Project_5/Data/Ted_info_'+str(count1)+'_'+str(count), 'wb'))

    teddict['Title'] = title
    teddict['Views'] = views
    teddict['Length'] = videolength
    teddict['Description'] = videodescription
    teddict['Author'] = author
    teddict['Keywords'] = keywords
    teddict['Event'] = event
    teddict['Upload Date'] = upload
    teddict['Profession'] = authorjob
    teddict['Year'] = year
    teddict['Speaker Description'] = speakerdescription
    teddict['Rating'] = rating
    teddict['Languages'] = languages
    teddict['Comments'] = comments
    teddict['Event Date'] = eventdate
    teddict['Links'] = weblinks
    pkl.dump(teddict, open('T/Users/ferdinandwohlenberg/Desktop/Projects/Project_5/Data/ed_info_dict', 'wb'))
    return teddict


#Functions to collect transcript and Comments
def gettranscript(links, count1):
    d_transcript = defaultdict(str)
    driver = webdriver.Chrome(chromedriver)
    count = count1
    for link in links:
        count += 1
        try:
            url = 'https://www.ted.com'+link+'/transcript'
            driver.get(url)
            soup = BeautifulSoup(driver.page_source,'lxml')
            transcript = ''
            for i in soup.find_all('a', class_ ='t-d:n hover/bg:gray-l.5' ):
                text1 = i.text.replace('\n', '')
                transcript = transcript + text1
            d_transcript[link] = transcript
        except:
            continue
        if count % 500 == 0:
            pkl.dump(d_transcript, open('/Users/ferdinandwohlenberg/Desktop/Projects/Project_5/Data/Transcripts_'+str(count1)+'_'+str(count), 'wb'))
        print(count)
    return d_transcript

def getcomments(links, count1):
    d_comments = defaultdict(str)
    driver = webdriver.Chrome(chromedriver)
    count = count1
    for link in links:
        count += 1
        try:
            url = 'https://www.ted.com'+link+'/discussion'
            driver.get(url)
            soup = BeautifulSoup(driver.page_source,'lxml')
            comments = []
            for comment in soup.find_all('div', class_= 'comment__body hyphens'):
                comments.append(comment.text.strip())
            d_comments[link] = comments
        except:
            continue
        if count%500 == 0:
            pkl.dump(d_comments, open('/Users/ferdinandwohlenberg/Desktop/Projects/Project_5/Data/Comments_'+str(count1)+'_'+str(count), 'wb'))
        print(count)
    return d_comments


#Calling functions to collect informations

#Collecting video links
weblinks, brokenpages = scrapelinks()
links = scrapebrokenpages(weblinks, brokenpages)

#Collecting video information
d = scrapeinfo(links, 0)
pkl.dump(d, open('/Users/ferdinandwohlenberg/Desktop/Projects/Project_5/Data/video_info.pkl', 'wb'))

#Collecting Transcripts
d_transcript = gettranscript(links, 0)
pkl.dump(d_transcript, open('/Users/ferdinandwohlenberg/Desktop/Projects/Project_5/Data/Transcripts.pkl', 'wb'))

#Collecting Comments
d_comments = getcomments(links, 0)
pkl.dump(d_comments,open('/Users/ferdinandwohlenberg/Desktop/Projects/Project_5/Data/Comments.pkl', 'wb'))
