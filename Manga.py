from PyPDF2 import PdfFileMerger, PdfFileReader
from selenium import webdriver
from PIL import Image
import requests
import time
import os

def merge_pdf_pages(path, chapter_name):
    mergedObject = PdfFileMerger()
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if "Page" in filename:
            mergedObject.append(PdfFileReader(file_path, 'rb')) 
            os.remove(file_path)
    mergedObject.write(os.path.join(path, str(chapter_name) + ".pdf"))


def save_page_as_pdf(image_url, folder_path, page_number):
    succed = False
    while not succed:
        try:
            image_data = requests.get(image_url).content
            image_path = os.path.join(folder_path, 'Page_' + str(page_number) + '.jpg')
            with open(image_path, 'wb') as handler:
                handler.write(image_data)
            image_png = Image.open(image_path)
            image_saver = image_png.convert('RGB')
            image_saver.save(os.path.join(folder_path, 'Page_' + str(page_number).zfill(3)+'.pdf'))
            os.remove(image_path)
            succed = True
        except:
            succed = False


def split_input_line(line):
    line = line.split()
    url = line[0]
    if len(line) == 1:
        return url, 0, -2
    params = line[1].split('-')
    lower = int(params[0]) if params[0] != "x" else 0
    upper = int(params[1]) if params[1] != "x" else -1

    return url, lower, upper


def create_dir(file_path):
    if not os.path.exists(file_path):
        os.makedirs(file_path)


def find_first(lower, driver, url):
    driver.get(url)
    chapters_list = driver.find_element_by_xpath('//*[@id="chapter-list"]/div[2]/ul')
    chapters = chapters_list.find_elements_by_tag_name('li')
    driver.get(get_a_chapter(driver, chapters))
    chapters = driver.find_element_by_xpath("//*[@id=\"reader-wrapper\"]/div[2]/div[3]/div[4]/div/ul").find_elements_by_tag_name('li')
    for chapter in chapters:
        if chapter.find_element_by_tag_name('a').get_attribute('href').split('/')[-1] == 'capitulo-' + str(lower):
            driver.get(chapter.find_element_by_tag_name('a').get_attribute('href'))
            return
    driver.get(chapters[-1].find_element_by_tag_name('a').get_attribute('href'))


def check_last_chapter(driver):
    try:
        element = driver.find_element_by_xpath("//*[@id=\"reader-wrapper\"]/div[2]/div[3]/div[3]")
        if "disabled" in element.get_attribute("class"):
            return False
    except:
        return False
    return True


def check_last_wanted(upper, driver):
    return driver.find_element_by_xpath("//*[@id=\"reader-wrapper\"]/div[2]/div[3]/div[2]/span[1]").find_element_by_tag_name('em').text != upper
   

def get_a_chapter(driver, chapters):
    while not len(chapters):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        chapters_list = driver.find_element_by_xpath('//*[@id="chapter-list"]/div[2]/ul')
        chapters = chapters_list.find_elements_by_tag_name('li')
    return chapters[0].find_element_by_tag_name('a').get_attribute('href') 


def setup_folder_path(url):
    Manga_Name = "_".join(url.split('/')[-2].split("-"))
    folder_path = os.path.join(os.path.join(os.getcwd(), 'Files'), Manga_Name)
    create_dir(folder_path)
    return folder_path


options = webdriver.ChromeOptions()
options.add_argument('headless')
driver = webdriver.Chrome(options = options)

input = open('mangas.txt', 'r')
input_lines = input.readlines()


for line in input_lines:
    url, lower, upper = split_input_line(line)
    folder_path = setup_folder_path(url)
    find_first(lower, driver, url)
    
    while (lower - (upper + 1)):
        succed = False
        while not succed:
            try:
                next_page_button = driver.find_element_by_xpath('//*[@id="reader-wrapper"]/div[9]/div[2]/div/div[3]')
                total_pages = int(driver.find_element_by_xpath('//*[@id="reader-wrapper"]/div[9]/div[2]/div/div[2]/span/em[2]').text)
                succed = True
            except:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        for i in range(1,total_pages+1):
            image_url = driver.find_element_by_xpath('//*[@id="reader-wrapper"]/div[4]/div[2]/div/img').get_attribute('src')
            save_page_as_pdf(image_url, folder_path, i)
            next_page_button.click()
            time.sleep(20)
        merge_pdf_pages(folder_path, "Capítulo_" + driver.find_element_by_xpath("//*[@id=\"reader-wrapper\"]/div[2]/div[3]/div[2]/span[1]").find_element_by_tag_name('em').text)
        lower += 1
        if not check_last_chapter(driver):
            break
        driver.find_element_by_xpath('//*[@id=\"reader-wrapper\"]/div[2]/div[3]/div[3]').click()
        time.sleep(60)