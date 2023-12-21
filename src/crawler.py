import requests
from bs4 import BeautifulSoup
from collections import deque, namedtuple
from urllib.parse import urlsplit, urlunsplit, urljoin
from socket import gethostbyname, gethostbyaddr
from os import getcwd
from os.path import normpath, abspath, dirname

class Crawler:

    # TODO pass logger
    # TODO refactor to test with mock-up html files
    def __init__(self):
        self._visited = set()
    
    # TODO implement a Strategy
    def crawl(self, url):
        parsed_url = urlsplit(url)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        '''
        Collect all links before crawling
        '''
        link = url
        current_links = []
        for tag in soup.find_all(['a', 'img', 'link', 'script']):
            if 'href' in tag.attrs:
                if self.is_link_on_host(tag['href'], parsed_url.host):
                    link = self.normalize_link(tag['href'], parsed_url.host)
            if 'src' in tag.attrs:
                if self.is_link_on_host(tag['src'], parsed_url.host):
                    link = self.normalize_link(tag['src'], parsed_url.host)
            if link not in current_links:
                current_links.append(link)

        '''
        Crawl each link
        '''
        for link in current_links:
            if link not in self._links:
                self._visited.add(url)
                self.crawl(self, link)
        
        print(self._visited)
        return self._visited
    
    def crawl_local(self, file_path):
        file_path = abspath(file_path)
        with open(file_path, 'r') as fp:
            soup = BeautifulSoup(fp, 'html.parser')
            current_links = self.scrape_links(soup)
        
        '''
        This is probably be bug-prone
        '''
        for link in current_links:
            split_link = urlsplit(link)
            if split_link.scheme == "":
                dir_name = dirname(file_path)
                link_path = ''.join([dir_name, split_link.path])
                normalized_link = abspath(link_path)
                if normalized_link not in self._visited:
                    self._visited.add(normalized_link)
                    self.crawl_local(normalized_link)

        return self._visited
    
    def crawl_web(self, root):
        response = requests.get(root)
        soup = BeautifulSoup(response.text, 'html.parser')

        # scrape every possible link
        current_links = self.scrape_links(soup)
        
        # CRAWLINGGG INNNNN MY SKINNNNN
        for link in current_links:
            normalized_link = self.normalize_link(link, root)
            if normalized_link is not None and normalized_link not in self._links:
                self._visited.add(normalized_link)
                self.crawl_web(self, normalized_link)
        return self._visited
    
    # this should be independent
    def scrape_links(self, soup):
        current_links = []
        for tag in soup.find_all(['a', 'img', 'link', 'script']):
            if 'href' in tag.attrs:
                link = tag['href']
            if 'src' in tag.attrs:
                link = tag['src']
            if link not in current_links:
                current_links.append(link)
        return current_links

    # TODO re-evaulate link building
    def normalize_link(self, link, root):
        if self.is_within_root_host(link, root):
            return urljoin(root, link)
        # TODO log the value of link
        return None

    # TODO consider refactoring this into some kind of HostIPManifest so we don't have to do round-trip dns lookups every time
    def is_within_root_host(self, link, root):
        parsed_link = urlsplit(link)
        parsed_root = urlsplit(root)
        ip_addr_root = None
        ip_addr_link = None
        if parsed_root.hostname is not None: # going to assume we've already looked this up before
            ip_addr_root = gethostbyname(parsed_root.hostname)
        if parsed_link.hostname is not None:
            ip_addr_link = gethostbyname(parsed_link.hostname)
        else: # if its None, assume its on the root host
            ip_addr_link = ip_addr_root
        return ip_addr_root == ip_addr_link