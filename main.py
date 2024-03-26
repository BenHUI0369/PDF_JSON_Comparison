from PyPDF2 import PdfReader
import fitz
import json
import re
import codecs
import os

upload_folder = 'uploads/'
result_folder = 'results/'

#global val
regexRules = r"<.*?>|[^，、。:\w%.,]|\s" #remove none text and number char
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

def cleanhtml(raw_html):
  global regexRules
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

def highlightPDF(outputFileName, pdfFileName, pdfNotFoundString):
  doc = fitz.open(pdfFileName)
  for page in doc:
    for text in pdfNotFoundString:
      text_instances = page.search_for(text)
      for inst in text_instances:
          highlight = page.add_highlight_annot(inst)
          highlight.update()
          
  doc.save(outputFileName, garbage=4, deflate=True, clean=True)

def process(jsonFileName, pdfFileName, outputFileName):
    # compare and generate output block function 

    # --- start 

    # Read json 
    # langJsonFile = open(jsonFileName)
    # langJson = json.load(langJsonFile)

    #for Windows cannot decode json file error
    with codecs.open(jsonFileName, 'r', encoding='utf-8') as lang_json_file:
        langJson = json.load(lang_json_file)
        lang_json_file.close()
    loopLangJson(langJson)
    pdfNotFoundString, pdfView = mergePDFContent(pdfFileName)
    highlightPDF(outputFileName, pdfFileName, pdfNotFoundString)
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