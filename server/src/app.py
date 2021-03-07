from flask import Flask, render_template, request, jsonify
import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Imports the Google Cloud client library
from google.cloud import language_v1
import mechanicalsoup
import bs4
import urllib
import ssl

import os
fileName = "hackathonstock-firebase-adminsdk-cekxm-23e863eaec.json"
scriptDir = os.path.dirname(os.path.realpath(__file__))
a = os.path.join(scriptDir, fileName)

ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__)

# Use a service account
if not firebase_admin._apps:
    cred = credentials.Certificate(a)
    firebase_admin.initialize_app(cred)
db = firestore.client()


# Instantiates the client for language processing
client = language_v1.LanguageServiceClient.from_service_account_json(a)


@app.route('/')
def index():
    return "Hello World!"

@app.route('/test')
def test():
    return "WOWEE"

@app.route('/check')
def check():
    return "1000"



@app.route('/calc', methods=['POST'])
def calcPercent():
    req = request.get_json()
    kw = req['keyword']
    if not kw:  return jsonify({"error": "Not Able to Process Further."}), 404
    doc_ref = db.collection(u'sentiments').document(kw.lower())
    doc = doc_ref.get()
    pos,neg = 0,0
    if doc.exists:
        get_pos= doc_ref.get({u'positive_cnt', u'negative_cnt'})
        atts = get_pos.to_dict()
        return jsonify({"positives":atts[u'positive_cnt'], "negatives":atts[u'negative_cnt']})
    else:
        n1,p1 = calcNytimes(kw)
        n2,p2 = calcForbes(kw)
        pos = p1 + p2
        neg = n1 + n2
        add_data(kw,(pos,neg))
    return jsonify({"positives":pos, "negatives":neg})

def calcForbes(keyword):
    browser2 = mechanicalsoup.StatefulBrowser()
    print("WORKING?")
    browser2.open("https://www.forbes.com/search/?q=%s" % (keyword))
    links = browser2.page.find_all(class_="stream-item et-promoblock-removeable-item et-promoblock-star-item")
    limit = 0
    neg_count = 0
    pos_count = 0
    for lk in links:
        if limit == 10:  break
        href = lk.a.get('href')
        browser2.open(href)
        body = browser2.page.find('div', {"class":"article-body fs-article fs-responsive-text current-article"})
        if not body:    continue
        txts = []
        contents = body.find_all('p')
        for ext in contents:
            txts.append(ext.getText())
        text = (" ".join(txts))
        document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)

        sentiment = client.analyze_sentiment(request={'document': document}).document_sentiment
        if sentiment.score < 0: neg_count += 1
        if sentiment.score > 0: pos_count += 1
        # results = dict(
        #     score=f"{sentiment.score:.1%}",
        #     magnitude=f"{sentiment.magnitude:.1%}",
        # )
        # for k, v in results.items():
        #     print(f"{k:10}: {v}")
        limit += 1
    browser2.close()
    return (neg_count,pos_count)    

def calcNytimes(keyword):
    browser = mechanicalsoup.StatefulBrowser()
    browser.open("https://www.nytimes.com/search?query=%s" % (keyword))
    links = browser.page.find_all(class_="css-1l4w6pd")
    base = 'https://www.nytimes.com'
    limit = 0
    neg_count = 0
    pos_count = 0
    for lk in links:
        if limit == 10:  break
        href = lk.a.get('href')
        full = base + href
        browser.open(full)
        body = browser.page.find('section', {"name":"articleBody"})
        if not body:    break
        txts = []
        contents = body.find_all('p')
        for ext in contents:
            txts.append(ext.getText())
        text = (" ".join(txts))
        document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)

        sentiment = client.analyze_sentiment(request={'document': document}).document_sentiment
        if sentiment.score < 0: neg_count += 1
        if sentiment.score > 0: pos_count += 1
        # results = dict(
        #     score=f"{sentiment.score:.1%}",
        #     magnitude=f"{sentiment.magnitude:.1%}",
        # )
        # for k, v in results.items():
        #     print(f"{k:10}: {v}")
        limit += 1
    browser.close()
    return (neg_count,pos_count)

def calcWallst(keyword):
    browser3 = mechanicalsoup.StatefulBrowser()
    browser3.open("https://www.cnn.com/search?q=%s&size=10&category=business" % (keyword))
    print(browser3.page)
    links = browser3.page.find_all(class_="cnn-search__result cnn-search__result--article")
    print(links)
    limit = 0
    neg_count = 0
    pos_count = 0
    for lk in links:
        if limit == 10:  break
        href = lk.a.get('href')
        browser3.open(href)
        body = browser3.page.find('div', {"class":"middle-column"})
        print(body)
        if not body:    break
        txts = []
        contents = body.find_all('p')
        for ext in contents:
            txts.append(ext.getText())
        text = (" ".join(txts))
        document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)

        sentiment = client.analyze_sentiment(request={'document': document}).document_sentiment
        if sentiment.score < 0: neg_count += 1
        if sentiment.score > 0: pos_count += 1
        results = dict(
            score=f"{sentiment.score:.1%}",
            magnitude=f"{sentiment.magnitude:.1%}",
        )
        for k, v in results.items():
            print(f"{k:10}: {v}")
        limit += 1
    browser3.close()
    return (neg_count,pos_count)

def add_data(keyword,tup):
    doc_ref = db.collection(u'sentiments').document(keyword)
    doc_ref.set({
        u'positive_cnt': tup[0],
        u'negative_cnt': tup[1]
    })
    print("Addition done!")
    return "Added data to the database!"
 


if __name__ == '__main__':
    calcWallst('tesla')
    #app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))