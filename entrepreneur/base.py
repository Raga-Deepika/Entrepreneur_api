from bs4 import BeautifulSoup as bs
from dateparser import parse
import re
import requests
import random
from entrepreneur import logger

desktop_agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
                 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']

proxies = {
    'http': 'http://35.173.16.12:8888/?noconnect',
    'https':'http://35.173.16.12:8888/?noconnect'
}



def proxied_request(url, extra_headers={}, params={}):
    headers = {
        'User-Agent':random.choice(desktop_agents),
        # 'Accept': ('text/html,application/xhtml+xml,application/xml;'
        #            'q=0.9,*/*;q=0.8'),
        # 'Accept-Language': 'en-US,en;q=0.8',
        # 'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    headers.update(extra_headers)

    # if url.startswith('http://'):
    #     p = proxies('http')
    # else:
    #     p = proxies('https')
    resp = requests.get(url, headers=headers, proxies=proxies, params=params)
    return resp


def entre_base(category, page=1):
    try:
        entrepreneurDict = {}
        entrepreneurDict['success'] = True
        base_url = 'https://www.entrepreneur.com'
        link ='{0}/topic/{1}/{2}'.format(base_url,category,str(page))
        try:
            s = requests.Session()
            request = s.get(link,proxies=proxies)
            prepared_request = s.prepare_request(request)
            response = s.send(prepared_request)
            soup = bs(response.content, 'lxml')
            logger.info('successful request to entrepreneur connector {0}  with category {1} for page {2}'.format(link,category,page))
        except Exception as e:
            entrepreneurDict['success'] = False
            entrepreneurDict['errorMessage'] = str(e)
            logger.warning('request to entrepreneur connector {0}  with category {1} failed: {2} for page {3}'.format(link,category,str(e),page))
            return entrepreneurDict
        posted_at = ''
        if response.status_code == 200:
            entrepreneurDict['data'] = []
            try:
                card = soup.find_all('div', class_='block')
            except AttributeError:
                card = []
                return entrepreneurDict
            try:
                unwanted_pages = soup.find('ul',class_='pagination').find_all('li')[-1]
                unwanted_pages.extract()
                total_pages = soup.find('ul',class_='pagination').find_all('li')[-1].text.strip()
            except Exception as e:
                logger.warning('error in finding the total pages :{0} for page {1} category {2}'.format(str(e),page,category))
                total_pages = 1
            entrepreneurDict['total_pages'] = total_pages
            for item in card:
                content = ''
                obj = {}
                try:
                    titles = item.find('h3').text.strip()
                except AttributeError:
                    titles = None
                try:
                    links = item.h3.a.get('href')
                    if 'https' in links:
                        url = links
                    else:
                        url = '{0}{1}'.format(base_url,links)
                except Exception as e:
                    logger.warning('Error with url of the details page: {0} category {1}'.format(str(e),category))
                    url = None
                try:
                    s = requests.Session()
                    request = s.get(url,proxies=proxies)
                    prepared_request = s.prepare_request(request)
                    response1 = s.send(prepared_request)
                    soup1 = bs(response1.content, 'lxml')
                    logger.info('request to the content url {0} of entrepreneur connector is successful for category {1} with page {2}'.format(url,category,page))
                except Exception as e:
                    logger.warning('request to the content url {0} of entreprenuer connector failed for category {1} page {2}: {3}'.format(url,category,page,str(e)))
                try:
                    snip = item.find('div', class_='deck')
                    if snip is None:
                        snip1 = soup1.find('div', class_='art-deck').text.strip()
                        obj['snippet'] = snip1
                    else:
                        obj['snippet'] = snip.text.strip()
                except AttributeError:
                    snip = None
                card1 = soup1.find('div', class_='art-v2-body')
                try:
                    date = card1.div.time.get('content')
                    posted_at = parse(date)
                except AttributeError:
                    posted_at = None
                try:
                    contents = card1.find_all({'p', 'ul'})
                    for ps in contents:
                        cont = ps.text.strip().replace('\xa0','')
                        cont = re.sub(r'[\n\r\t]','',cont)
                        content += cont
                except Exception as e:
                    logger.warning('error with the contents page {0} of entrepreneur category {1} : {2}'.format(url,category,str(e)))
                    content = None
                obj['title'] = titles
                obj['url'] = url
                obj['date'] = posted_at
                obj['content'] = content
                obj['category'] = category
                obj['source'] = 'entrepreneur'
                entrepreneurDict['data'].append(obj)
            return entrepreneurDict
    except Exception as e:
        logger.error('Error in scraping page {0} of the entrepreneur connector category {1}: {2}'.format(page,category, str(e)))
        return None