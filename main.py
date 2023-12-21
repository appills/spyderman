from src.crawler import Crawler


# TODO finish test script

crawler = Crawler()
results = crawler.crawl_local('./test/test.html')
print(results)