from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import csv
import json
import nltk
from nltk.corpus import stopwords
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


nltk.download('punkt')
nltk.download('stopwords')

wordfreq = {}
resultFreq = {}
bigramIndex = {}
def main():
    SITE = 'http://shakespeare.mit.edu'

    listOfLinks = getLinks(SITE)
    for link in listOfLinks:
        words = scrape(fetchFromURL, link)
        words.sort()
        wordCountDict = createDict(link, words)
    writeFileComplete(wordfreq)
    writeFileJson(wordfreq)
    print("CSV Report saved in Final.csv")
    print("JSON Report saved in data_file.json")
    bigramAsg()
    while(1):
        userQuery = input("\nPlease enter a term to search or type \"exit\" to exit: ")
        if userQuery == "exit":
            return
        searchInput(userQuery)

def searchInput(userQuery):
    Extrastopwords = [",",";",".",":","!","?","thou","thy","'",
                    "thee","--","hath","let","'ll"]
    stopWords = set(stopwords.words('english') + Extrastopwords)
    porter = nltk.PorterStemmer()
    normalizedQuery = porter.stem(userQuery.lower())
    if normalizedQuery in stopWords:
        print("\nThe term \"" + userQuery + "\" can not be identified.\nEnter again.\n")
    elif normalizedQuery in wordfreq:
        postingList = wordfreq[normalizedQuery]
        count = 0
        print("The term \"" + userQuery + "\" has been found in these documents:\n")
        for posting in postingList:
            if count > 0:
                print(posting)
            count += 1

    else:
        userQueryList = []
        userQueryList.append(userQuery)
        queryBigrams = searchBiagram(userQueryList)
        associatedTermsList = []
        NewTerms = []
        for bigram in queryBigrams:
            if bigram in bigramIndex:
                associatedTerms = bigramIndex[bigram]
                associatedTermsList.extend(associatedTerms)
        associatedTermsSet = set(associatedTermsList)
        for term in associatedTermsSet:
            termSet = set(term)
            querySet = set(userQuery)
            jDistance = nltk.jaccard_distance(termSet,querySet)
            if round(jDistance,2) <= 0.16:
                NewTerms.append(term)

        if len(NewTerms) == 0:
            print("The term \"" + userQuery + "\" can not be identified. \nEnter again.\n")
        else:
            print("The term \"" + userQuery +  "\" can not be found. Did you mean:\n")
            for NewTerm in NewTerms:
                print(NewTerm)


def searchBiagram(userSearch):
    userSearchIndex = {}
    for term in userSearch:
        indexTerm = '$' + term + '$'
        for i in range(len(indexTerm)-1):
            permutation = indexTerm[i:i+2]
            if permutation not in userSearchIndex:
                userSearchIndex[permutation] = [term]
            else:
                userSearchIndex[permutation].append(term)
    return userSearchIndex
        

def scrape(fetchFromURL, url):
    html = fetchFromURL(url)
    words = BeautifulSoup(html, 'html.parser').text.lower()

    for p in '`-=[]\\;\',./~!@#$%^&*()_+{}|:"<>?':
        words = words.replace(p,'')
    return words.split()


def createDict(url, listOfWords):
    title = ''

    if 'Poetry' not in url:
        title = url.split('/')[3]
    elif 'sonnet' in url:
        title = url.split('/')[4]
        splitTitle = title.split('.')
        title = splitTitle[0] + splitTitle[1]
    else:
        title = url.split('/')[4].split('.')[0]

    for word in listOfWords:
        if word not in wordfreq:
            wordfreq.setdefault(word, []).append(0)
            wordfreq.setdefault(word, []).append(title)
        wordfreq[word][0] += 1
        if title not in wordfreq[word]:
            wordfreq.setdefault(word, []).append(title)
       


def writeFileComplete(wordfreq):
    w = csv.writer(open("Final.csv", "w"))
    for key, val in wordfreq.items():
        w.writerow([key, val])


def writeFileJson(data):
    with open("data_file.json", "w") as write_file:
        json.dump(data, write_file)



def bigramAsg():
    for term in wordfreq:
        indexTerm = '$' + term + '$'
        for i in range(len(indexTerm)-1):
            permutation = indexTerm[i:i+2]
            if permutation not in bigramIndex:
                bigramIndex[permutation] = [term]
            else:
                bigramIndex[permutation].append(term)

    w = csv.writer(open("Final_Bigram.csv", "w"))
    for key, val in bigramIndex.items():
        w.writerow([key, val])
    print('Bigram CSV Document Created : Final_Bigram.csv ')
    with open("Final_Bigram.json", "w") as write_file:
        json.dump(bigramIndex, write_file)
    print('Bigram JSON Document Created: Final_Bigram.json ')


##
########## TXT WRITER ##########
##        outputFile = open(title + '.txt', 'w')
##        for word in wordDict:
##             outputFile.write(word + " = " + str(wordDict[word]) + '\n')
##        outputFile.close()

############ CSV WRITER ##########
##    with open(title + '.csv', 'w') as f:
##        writer = csv.writer(f)
##        for key in wordDict:
##            writer.writerow([key, wordDict[key]])
##



def getLinks(url):
    linkList = []

    rawText = fetchFromURL(url)
    links = get_target_urls(rawText)

    for i in links:
        if 'http' not in i:
            linkList.append(url + "/" + i.replace('index','full'))

    for link in linkList:
        if 'sonnets' in link:
            sonnetLink = linkList.pop(linkList.index(link)) #http://shakespeare.mit.edu/Poetry/sonnets.html

    sonnetLinks = []
    rawText = fetchFromURL(sonnetLink)
    soup = BeautifulSoup(rawText, 'html.parser')
    for line in soup.find_all('a'):
        sonnetLinks.append(sonnetLink[0:34] + line.get('href'))
    del sonnetLinks[0]

    linkList += sonnetLinks
    
    return linkList


def fetchFromURL(url):
    """
    Attempt to fetch content from URL via HTTP GET request. If it's HTML/XML return otherwise
    don't do anything
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during request to {0}:{1}' . format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if response looks like HTML
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def log_error(e):
    """
    log those errors or you'll regret it later...
    """
    print(e)
 

def get_target_urls(target):
    """
    Example of isolating different parent elements to gather subsequent URLs
    """
    linkList = []
    
    soup = BeautifulSoup(target, 'html.parser')

    for row in soup.find_all('td'):
        for link in row.find_all('a'):
            linkList.append(link.get('href'))
            
    return linkList


main()
