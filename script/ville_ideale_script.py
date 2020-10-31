from ville_ideale_scraping import (villeIdealScraper, proxyExecution)
import pandas as pd
import time


if __name__ == '__main__':

    obj= proxyExecution()
    proxy_list= obj.collect()

    scraper= villeIdealScraper()
    scraper.proxy_list= proxy_list

    def reactivation_function():
        try:
            return scraper.scrap(arr) # global variable
        except:
            reactivation_function()

    past_score= pd.DataFrame()
    for arr in range(20):#: # there are 20 arrondissements in paris
        arr+= 1
        print("Arrondissement num {}".format(arr))
        # score= reactivation_function()
        score= scraper.scrap(arr)

        new_score= pd.DataFrame.from_dict(score)
        # new_score.to_csv("../good_data/saved/score_{}.csv".format(arr), index=False) # we never know
        past_score= pd.concat([past_score
                                  , new_score]).reset_index(drop=True)

        print("Time to sleep (10s)")
        time.sleep(10)

    past_score.to_csv("../good_data/saved/score_per_arr.csv", index=False)
