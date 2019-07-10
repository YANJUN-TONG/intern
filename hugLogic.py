
from flask import Flask, request, jsonify 
import json 
import string
import re
import requests
from bs4 import BeautifulSoup
from lxml import html 

class HTMLObject(object):
	def __init__(self, name='root', question=None, url=None, title=None, questionflag=False, procedureflag=False, procedurequestion=False):
		self.name = name
		self.question = question
		self.url = url
		self.title = title
		self.questionflag = questionflag
		self.procedureflag = procedureflag
		self.procedurequestion = procedurequestion
	def __repr__(self):
		return "Page: [%s]" % self.title




def page_related(soup, URL):

	stack=[]
	
	tex = soup.select('div#d4h5-main-content p')

	rel = soup.select('div.related-links a')
	def test(s, tee, i, URL):
		ParagraphText = tee.getText()
		URL = URL.replace(URL[URL.rindex('/')+1:],s['href'])
		r = requests.get(URL)
		pf = ("Procedure" in r.text)
		if 'If you would like' in ParagraphText:
			result = re.match(r"If you would like.*,|.", ParagraphText)  
			reply = result.group()
			reply = reply.replace("If you would like", "Would you like")		
			reply = reply.replace(",", "?")	
			reply = reply.replace(".", "?")	
			if s['href'].endswith('html'):
				temp = s['href'].replace('viewer', 'doc')
				stack.append(HTMLObject('RelatedOptional'+str(len(stack)), reply, URL, s.text, False, pf))
				
		elif "If you" in ParagraphText:
			result = re.match(r"If you.*,|.", ParagraphText)  
			reply = result.group()
			reply = reply.replace("If", "Do")		
			reply = reply.replace(",", "?")	
			reply = reply.replace(".", "?")	
			if s['href'].endswith('html'):
				temp = s['href'].replace('viewer', 'doc')
				stack.append(HTMLObject('RelatedOptional'+str(len(stack)), reply, URL, s.text, False, pf))
				
		elif "required" in ParagraphText:
			if s['href'].endswith('html'):
				temp = s['href'].replace('viewer', 'doc')
				stack.append(HTMLObject('RelatedMandatory'+str(len(stack)), None, URL, s.text, False, pf))

		elif "have to be fulfilled" in ParagraphText:
			if s['href'].endswith('html'):
				temp = s['href'].replace('viewer', 'doc')
				stack.append(HTMLObject('RelatedMandatory'+str(len(stack)), None, URL, s.text, False, pf))
		elif "more information" in ParagraphText:
			reply = "Do you need more information on: "+str(s.text)+"?"
			if s['href'].endswith('html'):
				temp = s['href'].replace('viewer', 'doc')
				stack.append(HTMLObject('RelatedMandatory'+str(len(stack)), reply, URL, s.text, False, pf))
		else: 
			return stack

	i = 0
	for te in tex:
		temp = te.select("cite.cite")
		if temp!=[]:
			for tee in temp: #more than one citation in the same paragraph
				for s in rel:
					if ''.join(tee.string.split()) in ''.join(s.text.split()):
						test(s, te, i, URL)
						i+=1
	return stack
	
def next_pages(soup, URL):
	stack = []
	i=0
	#end of procedure is not clear
	while i<14:
		next = soup.select('div#d4h5-main-container a.next')
		url = next[0]['href']
		URL = URL.replace(URL[URL.rindex('/')+1:],url)
		stack.append(HTMLObject('Next'+str(len(stack)), None, URL, next[0]['title']))
		r = requests.get(URL)
		soup = BeautifulSoup(r.text, 'lxml')
		stack[-1].procedureflag = ("Procedure" in soup.text)
		i+=1
	return stack

def procedure_steps(soup,URL):
	stack = []
	steps = soup.find_all("li", {"class" : "li step stepexpand"})
	rel = soup.select('div.related-links a')
	escape_char = re.compile(r'\\x[0123456789abcdef]+')
	for s in steps:
		test = "".join(list(s.strings))
		#test = test.encode('Cp1252')
		test = re.sub(escape_char, " ", test)
		#test = re.sub(r'[\xa0-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', test) #test.replace('\xa0','->')
		test = test.replace('\n','')
		test = test.replace('\r',' ')
		test = test.replace('\t',' ')
		test = re.sub(' +', ' ', test)
		test = re.sub('->->', '->', test)
		temp = s.select("cite.cite")
		if temp!=[]:  
			for relatedL in rel:
				if ''.join(temp[0].string.split()) in ''.join(relatedL.text.split()):
					# print("why " + temp[0].string)
					url = relatedL['href']
					urlt = URL.replace(URL[URL.rindex('/')+1:],url)
					r = requests.get(urlt, allow_redirects=False)
					print(r.status_code, r.headers['Location'])
					#print(r.text)
					soupT = BeautifulSoup(r.text, 'lxml')
					print(urlt)
					procedureflag = ("Procedure" in soupT.text)
					break
		else:
			urlt = URL
			procedureflag = False
		stack.append(HTMLObject("ProcedureStep"+str(len(stack)),None,urlt,test,False,procedureflag))
	return stack

def constuct_stack(soup, URL):
	return page_related(soup, URL) + next_pages(soup,URL)
	
	
	
	
	