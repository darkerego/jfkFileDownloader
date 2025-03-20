#!/usr/bin/env python3
###################################################################################
import typing

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options

import os
import argparse

try:
    os.mkdir('./files')
except FileExistsError:
    pass


class Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    def __init__(self, verbosity: int = 0):
        self.verbosity = verbosity


    def print(self, text: typing.Any, color: str):
        assert hasattr(self, color.upper())
        color_code = getattr(self, color.upper())
        text = str(text)
        return f"{color_code}{text}{self.RESET}"

    def good(self, text: typing.Any):
        prefix = self.GREEN + '[' + self.YELLOW + '+' + self.GREEN + ']' + self.RESET + ' '
        print(prefix + str(text))

    def info(self, text: typing.Any):
        prefix = self.BLUE + '[' + self.MAGENTA + '~' + self.BLUE + ']' + self.RESET + ' '
        print(prefix + str(text))

    def error(self, text: typing.Any):
        prefix = self.RED + '[' + self.BLUE + '!' + self.RED + ']' + self.RESET + ' '
        print(prefix + str(text))

    def debug(self, text: typing.Any):
        if self.verbosity > 0:
            prefix = self.MAGENTA + '[' + self.GREEN + 'debug' + self.MAGENTA + ']' + self.RESET + ' '
            print(prefix + str(text))



class JFKFileDownloader:

    def __init__(self, seek: int=1, verbosity: int = 0):
        self.start = seek
        self.verbosity = verbosity
        self.initialized: bool = False
        self.driver = self.setup_method()
        self.vars = {}
        self.printer = Color()


    def setup_method(self):
        self.initialized = True
        options = Options()
        options.headless = True  # Enable headless mode
        return webdriver.Firefox(options)


    def download_pdf(self, url: str):
        # Send a GET request to fetch the PDF
        self.printer.debug(f'Downloading: {url}')
        response = requests.get(url)
        file_name = url.split('/')[-1].strip()

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Open a file in write-binary mode and save the content
            with open(f'files/{file_name}', 'wb') as file:
                file.write(response.content)
            self.printer.good(f'PDF: {file_name} downloaded successfully!')
        else:
            self.printer.error('[!] Failed to retrieve the PDF. Status code: %s' %  response.status_code)

    def teardown_method(self):
        self.driver.quit()

    def download_all_files(self):
        self.driver.get("https://www.archives.gov/research/jfk/release-2025")
        self.driver.set_window_size(1680, 1018)
        self.driver.find_element(By.NAME, "DataTables_Table_0_length").click()
        dropdown = self.driver.find_element(By.NAME, "DataTables_Table_0_length")
        dropdown.find_element(By.XPATH, "//option[. = 'All']").click()
        self.driver.find_element(By.CSS_SELECTOR, "option:nth-child(6)").click()
        element = self.driver.find_element(By.CSS_SELECTOR, "html")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click_and_hold().perform()
        element = self.driver.find_element(By.CSS_SELECTOR, "html")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        element = self.driver.find_element(By.CSS_SELECTOR, "html")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).release().perform()
        for doc in range(self.start, 2182):
            self.printer.info('Processing: %s' % doc)
            dl_url = self.driver.find_element(By.XPATH, f"/html/body/div[1]/div/div[2]/div/div/div/div/div[1]/section/div[3]/div[2]/div/table/tbody/tr[{doc}]/td[1]/a").get_attribute('href')
            self.download_pdf(dl_url)

    def main(self):
        self.download_all_files()
        self.teardown_method()


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('-s', '--seek', type=int, default=1, help='Start from a certain document number.')
    args.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity.')
    args = args.parse_args()
    t=JFKFileDownloader(args.seek, args.verbose)
    t.main()