import pandas as pd
import numpy as np
import datetime
import pickle as pkl
from collections import defaultdict
from collections import OrderedDict
import re
import string
from guess_language import guess_language
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import nltk
set(stopwords.words('english'))

from sklearn.decomposition import NMF
from sklearn.metrics import pairwise_distances
from gensim import corpora, models, similarities, matutils
from nltk.stem.porter import *
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
from nltk.util import ngrams
from nltk.stem import WordNetLemmatizer

from wordcloud import WordCloud, STOPWORDS

stopwords1 = stopwords.words('english')
stopwords1.append('just')
stopwords1.append('like')
stopwords1.append('com')
stopwords1.append('great')
stopwords1.append('might')
stopwords1.append('talk')
stopwords1.append('went')
stopwords1.append('ca')
stopwords1.append('laughter')
stopwords1.append('actually')
stopwords1.append('fact')
stopwords1.append('nan')
stopwords1.append('ok')
stopwords1.append('yeah')
stopwords1.append('quot')
stopwords1.append('wa')
stopwords1.append('ha')
stopwords1.append('see')
stopwords1.append('well')
stopwords1.append('would')
stopwords1.append('thats')
stopwords1.append('thing')
stopwords1.append('look')
stopwords1.append('im')
stopwords1.append('one')
stopwords1.append('get')
stopwords1.append('know')
stopwords1.append('think')
stopwords1.append('two')
stopwords1.append('say')
stopwords1.append('dont')
stopwords1.append('felt')

nmf_mat=pkl.load(open('/Users/ferdinandwohlenberg/Desktop/Projects/Project_5/Flask/data/NMF_Mat.pkl', 'rb'))
nmf=pkl.load(open('/Users/ferdinandwohlenberg/Desktop/Projects/Project_5/Flask/data/NMF.pkl', 'rb'))
dist=pkl.load(open('/Users/ferdinandwohlenberg/Desktop/Projects/Project_5/Flask/data/Pairwise_dist.pkl', 'rb'))
df=pkl.load(open('/Users/ferdinandwohlenberg/Desktop/Projects/Project_5/Flask/data/df.pkl', 'rb'))
tfidf=pkl.load(open('/Users/ferdinandwohlenberg/Desktop/Projects/Project_5/Flask/data/tfidf.pkl', 'rb'))

### Non-Negative Matrix Factorization (NMF)

def cleaninput(text):
    """
    Clean text given by user
    """
    assert type(text) == str, report_error('Input is not a string', text)

    #Check for english input texxt
    if guess_language(text) != 'en':
        print('Please provide a proper english text as input')
        return
    text_new = remove_punctuation(text)
    text_new = remove_numbers(text_new)
    text_lower = text_new.lower()

    #Lemmatize text
    tokens = word_tokenize(text_lower)
    lemmatizer = WordNetLemmatizer()
    tokens_lemmatized = [lemmatization(lemmatizer, i) for i in tokens]
    text = ' '.join(tokens_lemmatized)
    return text

def searchkeywords(df, keyword, sort = 'Views', number = 5):
    assert type(keyword) == str
    df_keywords = df[df.Keywords_string.str.contains(keyword)]
    if len(df_keywords)>0:
        if sort=='Views' or sort=='Relevance':
            df_keywords = df_keywords.sort_values(by= 'Views', ascending = False)
        elif sort=='Upload Date':
            df_keywords = df_keywords.sort_values(by= 'Timestamp', ascending = False)
        return df_keywords.iloc[0:number]
    else:
        return 'No Keywords detected'

def checkoverlap(text, vectorizer):
    text_list=text.split(' ')
    vectorizer_names =vectorizer.get_feature_names()
    count = 0
    for word in text_list:
        if word in vectorizer_names:
            count+=1
    if count > 0:
        return True
    else:
        print('Please rephrase your input/wording.')
        return False

def recommendation(text, df = df,nmf=nmf, nmf_mat=nmf_mat, dist=dist, sort='Relevance', number =5):
    recc=dist.argsort(axis=1)[:,0:number+1]
    text = text.lower()

    link = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    if link != []:
        link = link[0]
        index = link.find('talks')
        if index == -1:
            print('This link is not a valid Ted Talk Link')
            return 'This link is not a valid Ted Talk Link'
        else:
            link = link[index-1:]
            index_link = list(df[df.Links == link].index)
            print(index_link)
            print(type(index_link))
            recc1 = recc[index_link[0]][1:]
            return recc1
    elif len(text.split(' ')) <3:
        recommendations_keywords = searchkeywords(df, keyword = text, sort = sort, number = number)
        if type(recommendations_keywords) != str:
            if len(recommendations_keywords) > 0 and len(recommendations_keywords)<number:
                missing=number-len(recommendations_keywords)
                top_recc = list(recommendations_keywords.index)
                similar_docs=recc[top_recc[0]][1:]
                for k in range(missing):
                    top_recc.append(similar_docs[k])
                return top_recc

            elif len(recommendations_keywords)==number:
                return list(recommendations_keywords.index)
        else:
            #cleaned =cleaninput(text)
            if checkoverlap(text,tfidf):
                cv_new = tfidf.transform([text])
            else:
                return 'No results found'
    else:
        #cleaned = cleaninput(text)
        if checkoverlap(text, tfidf):
            cv_new = tfidf.transform([text])
        else:
            return 'No results found'

    nmf_new = nmf.transform(cv_new)
    dist = pairwise_distances(nmf_new,nmf_mat)
    recc=dist.argsort(axis=1)[:,0:number]
    return recc

def recommendoutput(recommender, sort='Relevance'):
    """
    Converts the array given as output from the recommendation function to a
    list of names of most similar articles.
    """
    if type(recommender)== str:
        return []
    else:
        if len(recommender)==1 and type(recommender[0]) != int:
            recommender = recommender[0]
        if sort=='Views':
            df_temp=df[df.index.isin(recommender)].sort_values(by='Views', ascending=False)
            recommender=list(df_temp.index)
        elif sort=='Upload Date':
            df_temp=df[df.index.isin(recommender)].sort_values(by='Timestamp', ascending=False)
            recommender=list(df_temp.index)
        name_list = [(df.Title.iloc[i], 'https://www.ted.com'+str(df.Links.iloc[i]), df.Author.iloc[i], df.Date_string.iloc[i]) for i in recommender]
        return name_list


def recommendationsystem(text,df = df,nmf=nmf, nmf_mat=nmf_mat, dist=dist,sort='Relevance', number = 5):
    recc = recommendation(text=text,df=df,nmf=nmf,nmf_mat=nmf_mat,dist=dist, sort=sort,number=number)
    print(recc)
    return recommendoutput(recc, sort=sort)
