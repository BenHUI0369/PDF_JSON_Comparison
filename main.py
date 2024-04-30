# using PdfReader will result in some error chinese test
from PyPDF2 import PdfReader
import fitz
import json
import re
import codecs
import os
import pdfplumber
# try to use pdfminer.six
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine
from pdfminer.high_level import extract_text
from bs4 import BeautifulSoup
import difflib

upload_folder = 'uploads/'
result_folder = 'results/'

#global val
# regexRules = r"<.*?>|[^，、。:\w%.,]|\s" #remove none text and number char
# Keep Chinese characters, English letters, and digits
regexRules = r"[^\u4e00-\u9fffA-Za-z0-9]+"
# regex for removing the html test in json file (for pdfplumber)
regex_no_html_text = r"<[^>]+>"
langJsonStr = "" #Json string that compare with PDF string
ignoreKeys = [
  'url',
  'keywords',
  'type',
  'image',
  'id',
  'note',
  'class',
  'see-more-in-stories',
  'href',
  'local',
  'src',
  'alt',
  'jpg',
  'icon',
  'color',
  'backgroundColor',
  'link',
  'bg',
  'icon-class',
  'path',
  'meta',
  'pointBorderColor',
  'ul-class',
  'mobile-svg',
  'custom-class',
  'svg',
  'to',
  'size',
  'filterType',
  'filterKey',
  'borderColor',
  'breadcrumb-title'
]
pdfView = []
pdf_all_text_output = []

def cleanhtml(raw_html):
  global regexRules
  if '<' in raw_html:
     edited_html = BeautifulSoup(raw_html, 'html.parser')
     raw_html = edited_html.get_text()
  cleantext = re.sub(regexRules, '', raw_html)
  return cleantext

def loopLangJson(json, key = None, prefix = None):
  global ignoreKeys, langJsonStr

  if(key in ignoreKeys):
    return
  
  if(type(json) is not str and type(json) is not dict and type(json) is not list):
    return
  
  if(type(json) is dict):
        for i in json:
          _key = i
          if(prefix != None):
            _key = prefix + "." + _key
          loopLangJson(json[i], i, _key)
        return
  
  if(type(json) is list):
        _index = 0
        for i in json:
          _key = str(_index)
          if(prefix != None):
            _key = prefix + "." + _key
          loopLangJson(i, str(_index), _key)
          _index = _index + 1
        return
  
  langJsonStr = langJsonStr + cleanhtml(json)

# using PdfReader
'''
def mergePDFContent(file):
    global langJsonStr, regexRules
    # print(langJsonStr)
    pdfNotFoundString = []
    pdfView = []
    reader = PdfReader(file)
    for page in reader.pages:
      splitlinePage = page.extract_text().splitlines()
      for i in splitlinePage:
        # print(i)
        _search = re.sub(regexRules, '', str(i))
        # print(_search)
        pdfView.append(_search)
        if langJsonStr.find(_search) == -1:
          pdfNotFoundString.append(i)
    return pdfNotFoundString, pdfView
'''

# help save pdfreading output for testing

def PDFTextOutput(file):
   global pdf_all_text_output
   with pdfplumber.open(file) as pdf:
      for page in pdf.pages:
         text = page.extract_text()
         if text:
            splitlinePage = text.splitlines()
            for i in splitlinePage:
               pdf_all_text_output.append(i)


# using pdfplumber

def mergePDFContent(file):
    global langJsonStr, regexRules
    pdfNotFoundString = []
    pdfView = []
    
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:  # Ensure there is text on the page
                splitlinePage = text.splitlines()
                for line in splitlinePage:
                    if '•' in line:
                       items = line.split('•')
                    else:
                       items = [line]
                    for item in items:
                        if item:  # Ensure the item is not empty
                            _search = re.sub(regexRules, '', item)
                            pdfView.append(_search)
                            if langJsonStr.find(_search) == -1:
                                pdfNotFoundString.append(item)
    return pdfNotFoundString, pdfView


def highlightPDF(outputFileName, pdfFileName, pdfNotFoundString):
  doc = fitz.open(pdfFileName)
  for page in doc:
    for text in pdfNotFoundString:
      text_instances = page.search_for(text)
      for inst in text_instances:
          highlight = page.add_highlight_annot(inst)
          highlight.update()
          
  doc.save(outputFileName, garbage=4, deflate=True, clean=True)

''' 
# use difflib to highligh pdf
def highlightPDF(outputFileName, pdfFileName, pdfNotFoundString):

  doc = fitz.open(pdfFileName)
  #Create a long string for the pdf file
  pdfString = ''.join(pdfView)
  #Check the differences between the merged pdf & json strings character by character
  d = difflib.Differ()
  diffBothDirections = list(d.compare(pdfString, langJsonStr))
  #Copy the array for editing
  clearedDiffBothDirections = diffBothDirections[:]
  #Remove those items with "+ " as prefix (i.e. additional words from json); only those with prefix "- " or "  " left
  for item in diffBothDirections[:]:
      if item.startswith("+ "):
          clearedDiffBothDirections.remove(item)

  currentItemIndex = 0  # Start with the first item in the clearedDiffBothDirections list

  for page in doc:
    last_pos = (0, 0) #start from the top left corner of the file

    while currentItemIndex < len(clearedDiffBothDirections):
            text = clearedDiffBothDirections[currentItemIndex]  # Current item to search
            text_instances = page.search_for(text[2:], from_point=last_pos)  #as the items in the clearedDiffBothDirections have "- "/"  "prefix
            
            # if not text_instances:
            if len(text_instances)==0:
                # currentItemIndex-=1   #no need this as it doesnt go to the +=1 step below
                print(currentItemIndex)  #for monitoring the process
                break  # Exit the loop and move to the next page
                       # (as all items in the clearedDiffBothDirections must appear in the pdf)
            
            #The characters appear in both pdf & json
            if text.startswith("  "):
                #Change the coordinate so the next search will start from there
                last_pos = (text_instances[0].x1, text_instances[0].y0)
                currentItemIndex += 1
                continue
            
            #The characters appear in pdf only
            highlight = page.add_highlight_annot(text_instances[0])  # Highlight the first found instance only
            highlight.update()
            #Change the coordinate so the next search will start from there
            last_pos = (text_instances[0].x1, text_instances[0].y0)
            currentItemIndex += 1

  doc.save(outputFileName, garbage=4, deflate=True, clean=True)
  doc.close()
'''

def process(jsonFileName, pdfFileName, outputFileName):
    # compare and generate output block function 

    # --- start 

    # Read json 
    # langJsonFile = open(jsonFileName)
    # langJson = json.load(langJsonFile)

    #for Windows cannot decode json file error
    #   with codecs.open(jsonFileName, 'r', encoding='utf-8-sig') as
    with codecs.open(jsonFileName, 'r', encoding='utf-8-sig') as lang_json_file:
        langJson = json.load(lang_json_file)
        lang_json_file.close()
    loopLangJson(langJson)
    pdfNotFoundString, pdfView = mergePDFContent(pdfFileName)
    highlightPDF(outputFileName, pdfFileName, pdfNotFoundString)
    PDFTextOutput(pdfFileName)
    # The path to the file where you want to save the string
    file_path = "output.txt"
    PDF_file_path = "PDFNotFoundoutput.txt"
    PDF_all_text_path = "PDF_all_text.txt"
    global langJsonStr
    global pdf_all_text_output
    # Using the 'with' statement to open a file and ensure it gets closed properly
    with open(file_path, 'w', encoding='utf-8') as file:
      # Writing the string to the file
      file.write(langJsonStr)
    with open(PDF_file_path, 'w', encoding='utf-8') as file:
       for line in pdfNotFoundString:
          file.write(line + '\n')
    with open(PDF_all_text_path, 'w', encoding='utf-8') as file:
      for line in pdf_all_text_output:
        file.write(line + '\n')
    # --- end

    # If anything finished
    # print("DONE")

if __name__ == '__main__':

    # getting the variable from app.py
    import sys
    if len(sys.argv) > 3:

      jsonFileName = upload_folder + sys.argv[1]
      pdfFileName = upload_folder + sys.argv[2]
      outputFileName = result_folder + sys.argv[3]

      # Create a temporary directory if not exists
      os.makedirs(upload_folder, exist_ok=True)
      os.makedirs(result_folder, exist_ok=True)
      
      process(jsonFileName, pdfFileName, outputFileName)

    # testing
    # jsonFileName = "uploads/test.json"
    # pdfFileName = "uploads/report.pdf"
    # process(jsonFileName, pdfFileName)