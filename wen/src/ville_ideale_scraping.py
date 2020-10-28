import requests
import urllib
import re
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from random import random
from typing import (List)


class proxyExecution():

    def __init__(self, url: str= None):

        if url == None:
            self.url = "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
        else:
            self.url= url

        self.save_path= "../data/web_scraping/proxy_list.txt"
        self.listed_proxy= []
        self.good_prox= []
        pass

    def __collect_proxy_list(self):
        urllib.request.urlretrieve(self.url, self.save_path)

        f = open(self.save_path, "r")
        self.listed_proxy = f.read().split("\n")
        pass

    def collect(self) -> List[str]:
        self.__collect_proxy_list()
        return self.listed_proxy

    def __transform_proxy_http(self, proxy: str) -> str:
        return "http://" + proxy

    def __test_proxy_list(self, num: int= 20) -> None:
        # NE PAS EXECUTER SI ON VEUT GAGNER DU TEMPS
        # Pour raison de simpliciter, on cherche que les proxy qui ont un port 8080
        pat = re.compile('.:8080$')

        proxies_list = [l for l in self.listed_proxy \
                        if l in list(filter(pat.findall, self.listed_proxy))]

        for prox in proxies_list:
            if len(self.good_prox) <= num:
                try:
                    print(prox)

                    # On génère un User Agent aléatoire pour chaque proxy
                    software_names = [SoftwareName.CHROME.value]
                    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
                    user_agent_rotator = UserAgent(software_names=software_names,
                                                   operating_systems=operating_systems, limit=100)
                    proxies = {"http": self.__transform_proxy_http(prox),
                               "https": self.__transform_proxy_http(prox)}

                    user_agent = user_agent_rotator.get_random_user_agent()
                    headers = {"User-Agent": user_agent}

                    r = requests.Session()
                    r.headers.update(headers)
                    r.proxies.update(proxies)

                    # Connexion à la page (I found azlyris in a past project, which is in my opinion a good site
                    # for testing)
                    page = r.get("https://www.azlyrics.com/", proxies=proxies, headers=headers)

                    # Si la connexion est fructueuse, alors le proxy est stocké
                    self.good_prox.append(prox)
                except:
                    # Si je ne peux pas me connecter avec ce proxy, alors je teste le suivant
                    print("Not Good")
                    continue
            else:
                # Stop selection if we get {num} good proxies
                break
        print("End")
        pass


    def test(self) -> List[str]:
        self.__test_proxy_list()
        return self.good_prox


class villeIdealScraper():

    def __init__(self):
        self.base_url= "https://www.ville-ideale.fr/paris-9e-arrondissement"
        self.r= None
        self.proxy_list= None
        self.random_proxy_list= None
        pass

    def __generate_random_proxy(self) -> str:
        if self.proxy_list == None:
            try:
                collect_proxy = proxyExecution()
                self.proxy_list = collect_proxy.collect()
            except ValueError:
                print("Can't find proxy list. You must put in manually")
                pass
        else:
            self.random_proxy_list = sorted(self.proxy_list, key=lambda x: random())
            return self.random_proxy_list[0]

    def __transform_proxy_http(self, proxy: str) -> str:
        return "http://" + proxy


    def __generate_random_agent(self) -> None:
        software_names = [SoftwareName.CHROME.value]
        operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
        user_agent_rotator = UserAgent(software_names=software_names,
                                       operating_systems=operating_systems, limit=100)

        user_agent = user_agent_rotator.get_random_user_agent()
        headers = {"User-Agent": user_agent}

        self.r = requests.Session()
        self.r.headers.update(headers)
        pass

    def __scrap_invisble(self) -> None:
        proxy= self.__generate_random_proxy()
        self.__generate_random_agent()

        proxy_html_format = {"http": self.__transform_proxy_http(proxy),
                   "https": self.__transform_proxy_http(proxy)}

        self.r.proxies.update(proxy_html_format)
        # self.page= r.get()
        pass

    def scrap(self, arr: int, anonymous: bool= True):
        if anonymous:
            self.__scrap_invisble()


        pass



if __name__ == '__main__':

    obj= proxyExecution()
    proxy_list= obj.collect()

    scraper= villeIdealScraper()
    scraper.proxy_list= proxy_list
    # test
    arr= 13
    scraper.scrap(arr= arr)

