from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
import re
from configparser import ConfigParser
import requests
import time

config = ConfigParser()
config.read('config.ini')

options = Options()
options.headless = False
browser = webdriver.Firefox(options=options)
browser.get("https://my.freenom.com/clientarea.php?language=english")

def login(user,pasw):
    try:
        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.ID, "username"))).send_keys(user)
        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.ID, "password"))).send_keys(pasw)
        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/section[2]/div/div/div[2]/form[1]/div[1]/input"))).click()
    except Exception as e:
        print(e)
        discordWebhook("Error - Login to Freenom Failed")

def renewAllDomains():
    try:
        browser.implicitly_wait(5)#for slow internet
        browser.get("https://my.freenom.com/domains.php?a=renewals")
        element = WebDriverWait(browser,30).until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))
        domainsList = element.text.split('Renew This Domain')
        browser.implicitly_wait(15) #to allow tbody fully load
        
        days = None

        # extract 1. Domain name, days until it needs to be refreshed
        for d in range(len(domainsList)-1):
            domain = re.findall(r"[a-z0-9]+\.[a-z]+",domainsList[d])[0]
            daysUntilRenewal = re.findall(r'\d+', domainsList[d])[0]

            # find the next date to run this script
            if(days is None):
                days = daysUntilRenewal
            elif((daysUntilRenewal < days) and (daysUntilRenewal > 14)):
                days = daysUntilRenewal

            print("{0} Days left - {1}".format(daysUntilRenewal,domain))
            if(int(daysUntilRenewal) <= 14):
                WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/section[3]/div/div/div/form/table/tbody/tr[{0}]/td[5]/a".format(str(d+1))))).click()    
                #1 more click I didn't get to it because I don't have a soon expiring domain yet
                try:
                    #/html/body/div[1]/section[3]/div/div/div[1]/form/table/tbody/tr/td[4]/select
                    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/section[3]/div/div/div[1]/form/table/tbody/tr/td[4]/select/option[12]"))).click()
                    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id=\"formSubmit\"]"))).click()
                except Exception as e:
                    browser.refresh()
                    try:
                        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/section[3]/div/div/div[1]/form/table/tbody/tr/td[4]/select/option[12]"))).click()
                        WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id=\"formSubmit\"]"))).click()
                    except Exception as ee:
                        discordWebhook("Error - Freenom has encountered an error.")
                        
                renewAllDomains()
                #browser.get("https://my.freenom.com/domains.php?a=renewals")
        browser.quit()
        return 
    except Exception as e:
        print(e)
        discordWebhook("Error - Domain renewal failed")
        
def discordWebhook(message):
    if(config['notifications']['notifyMe'] == "True"):
        url = config['notifications']['webhookUrl']
        discordUsername = config['notifications']['userDiscord']
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        data = {"username": "FreenomNotifier", "content": ""+(discordUsername+" - "+message)+""}
        r = requests.post(url, json=data, headers=headers)
        return

def main():
    login(config['account']['user'],config['account']['pasw'])
    renewAllDomains()

if __name__ == "__main__":
    main()