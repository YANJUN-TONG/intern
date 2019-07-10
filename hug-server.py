#server
from flask import Flask, request, jsonify 
import json 
import string
import re
from hugLogic import *
import requests
from bs4 import BeautifulSoup
from lxml import html 

dictionary = {}

#global crypto_name
app = Flask(__name__) 
port = 5000
@app.route('/', methods=['POST'])
def root():
    data = json.loads(request.get_data())
    
    print('Data received: \n')
    print(data)
    if data['nlp']['entities']:
   # for ent in data['nlp']['entities']:
      #  if 'hana_version'in ent:
            crypto_name = data['nlp']['entities']['hana_version'][0]['value']
    else:
            crypto_name = data['conversation']['memory']['hana_version']['value'] 
    #try:
        # crypto_name = data['nlp']['entities']['hana_version'][0]['value']
        # pass
    # except KeyError:
        # crypto_name = data['nlp']['entities']['hana_version'][0]['value']
        # pass
    # else:
        # crypto_name = data['conversation']['memory']['hana_version']['value']
        # pass
    conversationID = data['conversation']['id']
    print(conversationID)
    version = re.sub("[A-Za-z\s]", "", crypto_name) 
    print(version[:3] + '.' + version[3:])
    URL = 'https://help.sap.com/viewer/2c1988d620e04368aa4103bf26f17727/'+version[:3] + '.' + version[3:]+'/en-US/a428e6802a454f34bd3599782060c116.html'
    r = requests.get(URL.replace('viewer','doc'))
    soup = BeautifulSoup(r.text, 'lxml')
    #stack = {}
    if conversationID in dictionary:
        dictionary[conversationID] = constuct_stack(soup,URL.replace('viewer','doc'))
    else:
        newDictionaryEntry = {
            conversationID : constuct_stack(soup,URL.replace('viewer','doc'))
            }
        dictionary.update(newDictionaryEntry)
    print(dictionary)
    return jsonify( 
     status=200, 
     replies=[{ 
      "type": "buttons",
     "content": {
       "title": "Okay, this is the documentation link:",
       "buttons": [
         {
           "title": soup.title.text,
           "type": "web_url",
           "value": URL
         }]
		}
     }, {
	  'type': 'text',
	  'content': 'Would you like me to guide you through it?'
	 }]
	) 
@app.route('/yes', methods=['POST']) 
def index():
	data = json.loads(request.get_data())
	conversationID = data['conversation']['id']
	
	if not dictionary[conversationID]:
		return jsonify( 
		 status=200, 
		 replies=[{
		  'type': 'text', 
		  'content': ' I have no more steps. '
		  }]
	)
	step = dictionary[conversationID][0]
	if (dictionary[conversationID][0].question is None or dictionary[conversationID][0].questionflag is True) and (dictionary[conversationID][0].procedureflag is False and dictionary[conversationID][0].procedurequestion is False):
		del dictionary[conversationID][:1]
		return jsonify( 
		 status=200, 
		 replies=[{
		  "type": "buttons",
		  "content": {
		  "title": "You need to do the following:\n" + step.title,
          "buttons": [
            {
             "title": "See in documentation",
             "type": "web_url",
             "value": step.url.replace('doc','viewer')
            }]
		   }
        }, {
		  'type': 'text', 
		  'content': ' Continue?'
		  }]
	) 
	elif dictionary[conversationID][0].procedurequestion is True:
		dictionary[conversationID][0].procedureflag = False
		r = requests.get(dictionary[conversationID][0].url)
		soup = BeautifulSoup(r.text, 'lxml')
		url = dictionary[conversationID][0].url
		del dictionary[conversationID][:1]
		dictionary[conversationID] = procedure_steps(soup,url) + dictionary[conversationID]
		step = dictionary[conversationID][0]
		del dictionary[conversationID][:1]
		return jsonify( 
		 status=200, 
		 replies=[{
		  "type": "buttons",
		  "content": {
		  "title": "You need to do the following:\n" + step.title,
          "buttons": [
            {
             "title": "See in documentation",
             "type": "web_url",
             "value": step.url.replace('doc','viewer')
            }]
		   }
        }, {
		  'type': 'text', 
		  'content': 'Continue?'
		  }]
		) 
	elif dictionary[conversationID][0].procedureflag is True:
		dictionary[conversationID][0].procedurequestion = True
		return jsonify( 
		 status=200, 
		 replies=[{
		  "type": "buttons",
		  "content": {
		  "title": "I detect a procedure in next step:\n" + step.title,
          "buttons": [
            {
             "title": "See in documentation",
             "type": "web_url",
             "value": step.url.replace('doc','viewer')
            }]
		   }
        }, {
		  'type': 'text', 
		  'content': 'Would you like me to guide you through it?'
		  }]
		) 
	elif dictionary[conversationID][0].questionflag is False:
		dictionary[conversationID][0].questionflag = True
		return jsonify( 
		 status=200, 
		 replies=[{ 
		  'type': 'text', 
		  'content': dictionary[conversationID][0].question
		  }]
		) 

@app.route('/no', methods=['POST']) 
def indexno():
	data = json.loads(request.get_data())
	conversationID = data['conversation']['id']
		
	if not dictionary[conversationID]:
		return jsonify( 
		 status=200, 
		 replies=[{
		  'type': 'text', 
		  'content': ' I have no more steps. '
		  }]
	)
	step = dictionary[conversationID][0]
	if (dictionary[conversationID][0].questionflag is True or dictionary[conversationID][0].procedurequestion is True) and dictionary[conversationID][1].procedureflag is False:
		del dictionary[conversationID][:1]
		step = dictionary[conversationID][0]
		del dictionary[conversationID][:1]
		print(dictionary[conversationID])
		return jsonify( 
		 status=200, 
		 replies=[{
		  "type": "buttons",
		  "content": {
		  "title": "You need to do the following:\n" + step.title,
          "buttons": [
            {
             "title": "See in documentation",
             "type": "web_url",
             "value": step.url.replace('doc','viewer')
            }]
		   }
        }, {
		  'type': 'text', 
		  'content': ' Continue?'
		  }]
	) 
	elif (dictionary[conversationID][0].questionflag is True or dictionary[conversationID][0].procedurequestion is True) and dictionary[conversationID][1].procedureflag is True:
		del dictionary[conversationID][:1]
		step = dictionary[conversationID][0]
		#del dictionary[conversationID][:1]
		print(dictionary[conversationID])
		dictionary[conversationID][0].procedurequestion = True
		return jsonify( 
		 status=200, 
		 replies=[{
		  "type": "buttons",
		  "content": {
		  "title": "I detect a procedure in next step:\n" + step.title,
          "buttons": [
            {
             "title": "See in documentation",
             "type": "web_url",
             "value": step.url.replace('doc','viewer')
            }]
		   }
        }, {
		  'type': 'text', 
		  'content': 'Would you like me to guide you through it?'
		  }]
	) 
	elif dictionary[conversationID][0].question is None or dictionary[conversationID][0].questionflag is False:
		print(dictionary[conversationID])
		return jsonify( 
		 status=200, 
		 replies=[{
		  'type': 'text', 
		  'content': 'If you want to end the procedure tell me goodbye, otherwise I will give you the next step.'
		  }]
		) 

@app.route('/errors', methods=['POST']) 
def errors(): 
  print(json.loads(request.get_data())) 
  return jsonify(status=200) 
 
app.run(port=port)