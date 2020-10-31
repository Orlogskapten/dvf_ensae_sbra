import requests
import urllib
import re
from lxml import html

from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from random import random
from typing import (List, Dict)


class proxyExecution():

    def __init__(self, url: str= None, save_path: str= "../good_data/web_scraping/proxy_list.txt"):

        if url == None:
            self.url = "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
        else:
            self.url= url

        self.save_path= save_path
        self.listed_proxy= []
        self.good_prox= []
        pass

    def __collect_proxy_list(self) -> None:
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
        # proxies_list = [l for l in self.listed_proxy]

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
        self.page= None
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

    def __generate_good_url(self, arr: int) -> str:
        return self.base_url + "_751{}".format(str(arr).zfill(2))

    # @tailrec
    def __activate_valide_scraper(self, url: str, verbose: bool= True) -> None:
        try:
            self.__scrap_invisble()
            self.page= self.r.get(url)
        except:
            if verbose:
                print("Not a good proxy")
            self.__activate_valide_scraper(url= url)
        pass

    def scrap(self, arr: int, anonymous: bool= True) -> Dict[str, List[str]]:
        global list_result
        pattern= re.compile("([\D]*)(\d{1}\S\d*)") # allow to separate col names and grades

        if anonymous: # work only with anonymous (flemme)
            url= self.__generate_good_url(arr= arr)
            self.__activate_valide_scraper(url= url)

            tree = html.fromstring(self.page.content)
            global_note = tree.xpath('//p[@id="ng"]/text()')
            table_note = tree.xpath('//table[@id="tablonotes"]//tr')

            dict_result= {"Arrondissement": [arr]}
            for t in table_note:
                row= t.text_content()
                list_result= [res for res in pattern.split(row) if res != '']
                dict_result[list_result[0]]= [list_result[1]]

            # add global grade
            dict_result["Note global"]= [global_note[0]]


            return dict_result
        else:
            print("Nono")
        pass
