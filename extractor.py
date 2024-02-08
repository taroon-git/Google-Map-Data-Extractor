from tkinter import *
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from time import sleep
import re
import requests
import openpyxl
from webdriver_manager.chrome import ChromeDriverManager

class GoogleMapsScraperApp:
    def __init__(self, master):
        self.master = master
        master.title("Google Map Data Extractor")
        master.geometry("1150x700")
        icon_path = r"C:\\Users\\MTT\\Desktop\\GoogleExtractor\\GoogleExtractor\\Extractor.ico"
        master.iconbitmap(icon_path)


        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)

        title_frame = Frame(master, bg="blue")
        title_frame.pack(side=TOP, fill=X, anchor=W)

        title = Label(title_frame, text="Google Map Data Extractor", relief=GROOVE, font=("Arial", 15, "bold"), bg="blue", anchor="w", fg='white')
        title.pack(side=LEFT, padx=2, fill=Y)

        Manage_Frame = Frame(self.master, bd=3, relief=RIDGE, bg="lightgrey", width=250)  
        Manage_Frame.pack(side=LEFT, fill=Y, pady=(0, 0), padx=(0,0))  


        self.label_count = Label(Manage_Frame, text="TOTAL DATA COUNT: 0", fg="white", bg="green", font=("Arial", 12, "bold"))
        self.label_count.grid(row=1, columnspan=2, pady=(20, 0), padx=10, sticky="ew")


        self.label_search = Label(Manage_Frame, text="KEYWORDS", fg="white", bg="red", font=("Arial", 15, "bold"), padx=10, pady=5, relief=RAISED, bd=3)

        self.label_search.grid(row=3, column=0, pady=(100,0), padx=10, sticky="w")
        self.entry_search = Entry(Manage_Frame, font=("Arial", 15, "bold"), bd=5)
        self.entry_search.grid(row=3, column=1, pady=(100,0), padx=20, sticky="w")

        self.label_location = Label(Manage_Frame, text="LOCATIONS", fg="white", bg='red', font=("Arial", 15, "bold"), padx=10, pady=5, relief=RAISED, bd=3)
        self.label_location.grid(row=4, column=0, pady=(50,0), padx=10, sticky="w")
        self.entry_location = Entry(Manage_Frame, font=("Arial", 15, "bold"), bd=5)
        self.entry_location.grid(row=4, column=1, pady=(50,0), padx=20, sticky="w")

        Manage_Frame.rowconfigure(0, minsize=2)

        self.button_start = Button(Manage_Frame, text="START", width=14, height=1, bd=5, font=("Arial", 10, "bold"), command=self.start_scraping, bg="green", fg="white")
        self.button_start.grid(row=5, column=0, padx=(0, 0), pady=(320, 0))

        self.button_stop = Button(Manage_Frame, text="STOP", width=14, height=1, bd=5, font=("Arial", 10, "bold"), command=self.stop_scraping, bg="red", fg="white")
        self.button_stop.grid(row=5, column=1, padx=(0, 190), pady=(320, 0))

        self.button_download = Button(Manage_Frame, text="DOWNLOAD", width=14, height=1, bd=5, font=("Arial", 10, "bold"), command=self.download_results, bg="blue", fg="white")
        self.button_download.grid(row=5, column=1, padx=(90, 0), pady=(320, 0))  

        self.status_bar = Label(master, text="Status: Ready to go...", bd=3, relief=SUNKEN, anchor=W, font=("Arial", 12, "bold"), fg='red')
        self.status_bar.pack(side=BOTTOM, fill=X)

        Details_Frame = Frame(self.master, bd=4, relief=RIDGE, bg="blue")
        Details_Frame.pack(side=RIGHT, fill=BOTH, expand=True)

        Table_Frame = Frame(Details_Frame, bd=4, relief=RIDGE, bg="black")
        Table_Frame.pack(side=TOP, fill=BOTH, expand=True)

        scroll_y = Scrollbar(Table_Frame, orient=VERTICAL)
        self.tree = ttk.Treeview(Table_Frame, columns=("NAME", "ADDRESS", "DEPARTMENT", "PHONE", "URL", "RATINGS", "TOTAL_REVIEWS", "AVAILABLE_TIMINGS","EMAIL ID"))
        self.tree['show']='headings'
        self.tree.heading("NAME", text="NAME")
        self.tree.heading("ADDRESS", text="ADDRESS")
        self.tree.heading("DEPARTMENT", text="DEPARTMENT")
        self.tree.heading("PHONE", text="PHONE")
        self.tree.heading("URL", text="URL")
        self.tree.heading("RATINGS", text="RATINGS")
        self.tree.heading("TOTAL_REVIEWS", text="TOTAL_REVIEWS")
        self.tree.heading("AVAILABLE_TIMINGS", text="AVAILABLE_TIMINGS")
        self.tree.heading("EMAIL ID", text="EMAIL ID")
        self.tree.pack(fill=BOTH, expand=1)
        column_width = master.winfo_width() // 9
        for col in ("NAME", "ADDRESS", "DEPARTMENT", "PHONE", "URL", "RATINGS", "TOTAL_REVIEWS", "AVAILABLE_TIMINGS", "EMAIL ID"):
            self.tree.column(col, width=column_width, anchor=CENTER)

        self.data_count = 0


    def start_scraping(self):
        self.button_start.config(state=tk.DISABLED)
        self.button_stop.config(state=tk.NORMAL)
        self.button_download.config(state=tk.NORMAL)

        self.clear_treeview()

        self.scraped_data = []  
        self.scraping_flag = True
        self.stop_flag = False

        self.update_status("Scraping in progress...")

        # Generate keyword-location combinations
        self.keyword_location_combinations = self.generate_combinations()

        # Start a thread for each combination

        for combination in self.keyword_location_combinations:
            threading.Thread(target=self.scrape_google_maps, args=(combination,)).start()

    def generate_combinations(self):
        keywords = [k.strip() for k in self.entry_search.get().split(',') if k.strip()]
        locations = [l.strip() for l in self.entry_location.get().split(',') if l.strip()]

        if not keywords or not locations:
            messagebox.showwarning("Input Error", "Please provide valid keywords and locations.")
            return []

        return [(k, l) for k in keywords for l in locations]

        

    def stop_scraping(self):
        self.stop_flag = True
        self.update_status("Stopped")

    def download_results(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])

        if file_path:
            try:
                data_frames = []

                for i, data in enumerate(self.scraped_data, start=1):
                    data_frames.append(pd.DataFrame([data], columns=["NAME", "ADDRESS", "DEPARTMENT", "PHONE", "URL", "RATINGS", "TOTAL_REVIEWS", "AVAILABLE_TIMINGS","EMAIL ID"]))

                scraped_df = pd.concat(data_frames, ignore_index=True)

                scraped_df.to_excel(file_path, index=False)

                messagebox.showinfo("Download Complete", "Results downloaded successfully!")
                self.update_status("Downloaded")

            except Exception as e:
                self.update_status(f"Error: {e}")


            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")


    def scrape_google_maps(self, combination):
        keyword, location = combination
        url = "https://www.google.com/maps"
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--headless")

        
        driver_path = ChromeDriverManager().install()

        chrome_service = webdriver.chrome.service.Service(driver_path)
        with webdriver.Chrome(service=chrome_service, options=options) as driver:

            try:
                # self.update_status(f"{keyword} in {location}")

                driver.get(url)
                driver.implicitly_wait(5)

                search_input = driver.find_element(By.NAME, "q")
                search_input.send_keys(f"{keyword} in {location}")
                search_input.send_keys(Keys.RETURN)

                while self.scraping_flag and not self.stop_flag:
                    for iteration in range(2):
                        try:
                            WebDriverWait(driver, 20).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "Nv2PK"))
                            )

                            result_locator = (By.CLASS_NAME, 'Nv2PK')
                            result_elements = WebDriverWait(driver, 20).until(
                                EC.presence_of_all_elements_located(result_locator)
                            )

                            i = 0
                            while i < len(result_elements) and self.scraping_flag and not self.stop_flag:
                                try:
                                    driver.execute_script("arguments[0].scrollIntoView();", result_elements[i])

                                    result_elements[i].click()

                                    sleep(2)

                                    
                                    name = self.extract_location_info(driver, "DUwDvf", "class")
                                    address = self.extract_location_info(driver, "rogA2c", "class")
                                    if not any(existing_data["NAME"] == name and existing_data["PHONE"] == phone for existing_data in self.scraped_data): 
                                        category = self.extract_location_info(driver, "DkEaL", "class")
                                        phone = self.extract_phone_number(driver)
                                        web_url = self.extract_web_url(driver) 
                                        ratings = self.extract_ratings(driver)
                                        total_reviews = self.extract_total_reviews(driver)
                                        timings = self.extract_available_timings(driver)
                                        email_id = self.extract_emails_from_web_url(web_url)

                                        self.scraped_data.append({
                                            "NAME": name,
                                            "ADDRESS": address,
                                            "DEPARTMENT": category,
                                            "PHONE": phone,
                                            "URL": web_url,
                                            "RATINGS": ratings,
                                            "TOTAL_REVIEWS": total_reviews,
                                            "AVAILABLE_TIMINGS": timings,
                                            "EMAIL ID": email_id,
                                        })

                                        self.tree.insert("", "end", values=(name, address, category, phone, web_url, ratings, total_reviews, timings, email_id))

                                        self.data_count += 1
                                        self.label_count.config(text=f"TOTAL DATA COUNT : {self.data_count}")

                                    WebDriverWait(driver, 20).until(
                                        EC.presence_of_element_located((By.CLASS_NAME, "Nv2PK"))
                                    )

                                    result_locator = (By.CLASS_NAME, 'Nv2PK')
                                    result_elements = WebDriverWait(driver, 20).until(
                                        EC.presence_of_all_elements_located(result_locator)
                                    )

                                except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
                                    i += 1
                                    continue

                                i += 1

                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                            sleep(5)

                        except TimeoutException:
                            break
                        else:
                            WebDriverWait(driver, 30).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "Nv2PK"))
                            )

            except Exception as e:
                self.update_status(f"Error: {e}")
                print(f"Error: {e}")

            finally:
                self.update_status("Scraping completed.")
                self.button_start.config(state=tk.NORMAL)
                self.button_stop.config(state=tk.DISABLED)
                driver.quit()




    def check_scraping_complete(self):
        # Check if all threads have completed
        if all(not thread.is_alive() for thread in threading.enumerate()):
            self.update_status("All scraping sessions completed.")
            self.button_start.config(state=tk.NORMAL)
            self.button_stop.config(state=tk.DISABLED)
            self.button_download.config(state=tk.NORMAL)

    

    def update_status(self, status_text):
        if hasattr(self, 'status_bar') and isinstance(self.status_bar, Label):
            self.status_bar.config(text=f"Status: {status_text}")
        else:
            print("Not found or invalid.")



    def extract_location_info(self, driver, identifier, locator_type="class"):
        try:
            element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((self.get_locator_strategy(locator_type), identifier))
            )
            return element.text.strip() if element.text else "Not available"

        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return "NA"

    def extract_phone_number(self, driver):
        try:
            phone_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label^="Phone:"] div.Io6YTe'))
            )
            return phone_element.text

        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return "__________"

    def extract_web_url(self, driver):
        try:
            web_url_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-item-id="authority"]'))
            )
            web_url = web_url_element.get_attribute('href')

            return web_url if web_url else "Not available"

        except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
            return "NA"

    def extract_ratings(self, driver):
        try:
            rating_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.F7nice span[aria-hidden="true"]'))
            )
            return rating_element.text

        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return "NA"

    def extract_total_reviews(self, driver):
        try:
            total_reviews_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.jANrlb span'))
            )
            return total_reviews_element.text

        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return "NA"

    def get_locator_strategy(self, locator_type):
        if locator_type == "class":
            return By.CLASS_NAME
        elif locator_type == "xpath":
            return By.XPATH
        elif locator_type == "css":
            return By.CSS_SELECTOR
        else:
            raise ValueError("Invalid locator_type. Use 'class', 'xpath', or 'css'.")
        
    def extract_emails_from_web_url(self, web_url):
        try:
            response = requests.get(web_url, timeout=10)
            response.raise_for_status()
            html_content = response.text

            emails_found = self.extract_emails_from_html(html_content)
            return emails_found
        except requests.RequestException as e:
            print(f"Error fetching HTML content: {e}")
            return []

    @staticmethod
    def get_html_content(url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching HTML content: {e}")
            return "NA"

    @staticmethod
    def extract_emails_from_html(html_content):

        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        
        matches = re.findall(email_regex, html_content)

        return matches
    

    def extract_available_timings(self, driver):
        try:
            # Locate the button element using the provided class name
            timings_button = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'OMl5r'))
            )

            # Click the button to open the timings dropdown
            timings_button.click()

            # Locate the table element containing timings data
            timings_table = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'eK4R0e'))
            )

            # Extract data from each row (tr) inside the table
            timings_rows = timings_table.find_elements(By.CLASS_NAME, 'y0skZc')

            timings_data = []

            for row in timings_rows:
                # Extract day name from the first column (td with class 'ylH6lf')
                day_element = row.find_element(By.CLASS_NAME, 'ylH6lf')
                day = day_element.text.strip()

                # Extract timings from the second column (td with class 'mxowUb')
                timings_element = row.find_element(By.CLASS_NAME, 'mxowUb')
                timings_list = timings_element.find_elements(By.CLASS_NAME, 'G8aQO')

                # Combine day name and timings into a string
                timings_info = f"{day}: {' '.join([timings.text.strip() for timings in timings_list])}"

                timings_data.append(timings_info)

            return "  ".join(timings_data)

        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return "NA"

    def clear_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)


root = tk.Tk()
app = GoogleMapsScraperApp(root)
root.mainloop()