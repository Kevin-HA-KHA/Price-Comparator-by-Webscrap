import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import json

# Configuration du WebDriver
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    )
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Fonctions utiles
def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def accept_cookies(driver, selectors):
    try:
        cookie_button = driver.find_element(By.CSS_SELECTOR, selectors["cookies"])
        if cookie_button:
            cookie_button.click()
            time.sleep(1)
    except Exception:
        pass

def scrape_site(driver, url, search_term, selectors):
    data = []
    driver.get(url)
    time.sleep(1)
    accept_cookies(driver, selectors)

    search_bar = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selectors["search_bar"]))
    )
    search_bar.click()
    time.sleep(1)

    navbar = driver.find_element(By.CSS_SELECTOR, selectors["navbar"])
    navbar.click()
    search_input = driver.find_element(By.CSS_SELECTOR, selectors["search_input"])
    search_input.clear()
    search_input.send_keys(search_term)
    search_input.click()
    time.sleep(1)
    search_input.send_keys(Keys.RETURN)
    time.sleep(2)

    scroll_to_bottom(driver)

    products = driver.find_elements(By.CSS_SELECTOR, selectors["products"])
    for product in products:
        try:
            brand = product.find_element(By.CSS_SELECTOR, selectors["brand"]).text.strip()
        except:
            brand = "Non disponible"

        try:
            title = product.find_element(By.CSS_SELECTOR, selectors["title"]).text.strip()
        except:
            title = "Non disponible"

        price = product.find_elements(By.CSS_SELECTOR, selectors["price1"])
        if price:
            price = price[0].text.strip()
        if not price:
            price = product.find_elements(By.CSS_SELECTOR, selectors["price2"])
            if price:
                price = price[0].text.split(" ")[-1].strip()
            else:
                price = "Non disponible"

        try:
            volume = product.find_element(By.CSS_SELECTOR, selectors["volume"]).get_attribute('innerHTML').strip()
        except:
            volume = "Non disponible"
            if volume == "":
                volume = "Non disponible"

        data.append({
            "Marque": brand,
            "Titre": title,
            "Volume": volume,
            "Prix en euro": price
        })

    return data

# Interface Streamlit
st.title("Comparateur de prix de produits")
st.write("Choisissez un site et entrez le terme de recherche pour lancer le scraping.")

site_options = {
    "Sephora": "https://www.sephora.fr/",
    "Marionnaud": "https://www.marionnaud.fr/"
}

site_choice = st.selectbox("Choisir le site", list(site_options.keys()))
search_term = st.text_input("Terme de recherche", "Nina Ricci")
lancer_scraping = st.button("Lancer le scraping")

if lancer_scraping:
    try:
        with open("selectors.json", "r") as s:
            selectors = json.load(s)

        driver = init_driver()
        site_url = site_options[site_choice]
        site_data = scrape_site(driver, site_url, search_term, selectors[site_choice])

        driver.quit()

        df = pd.DataFrame(site_data)
        df["Prix en euro"] = df["Prix en euro"].str.replace(",", ".").str.replace("\u20ac", "").astype(float, errors='ignore')

        st.write("### Résultats du scraping")
        st.dataframe(df)

        file_name = "resultats_scraping.xlsx"
        df.to_excel(file_name, index=False)
        st.success("Scraping terminé. Fichier Excel généré.")
        st.download_button(
            label="Télécharger les résultats en Excel",
            data=open(file_name, "rb").read(),
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Erreur lors du scraping : {str(e)}")
