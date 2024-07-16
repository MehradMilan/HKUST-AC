import HKUST.constants as consts
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException

class HKUST(webdriver.Chrome):

    def __init__(self,
                 teardown: bool = True,):
        self.teardown = teardown
        super(HKUST, self).__init__()
        self.implicitly_wait(15)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.teardown:
            self.quit()
        
    def land_login_page(self):
        self.switch_to.new_window('window')
        self.get(consts.BASE_URL)   

    def submit_username(self, username):
        WebDriverWait(self, 15).until(EC.presence_of_element_located((By.ID, 'i0116')))
        username_input = self.find_element(By.ID, 'i0116')
        username_input.send_keys(username)
        username_button = self.find_element(By.ID, 'idSIButton9')
        username_button.click()

    def submit_password(self, password):
        self.implicitly_wait(5)
        WebDriverWait(self, 15).until(EC.presence_of_element_located((By.ID, 'i0118')))
        password_input = self.find_element(By.ID, 'i0118')
        password_input.send_keys(password)
        WebDriverWait(self, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[data-report-event="Signin_Submit"]')))
        password_button = self.find_element(By.CSS_SELECTOR, 'input[data-report-event="Signin_Submit"]')
        try:
            password_button.click()
        except StaleElementReferenceException:
            WebDriverWait(self, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[data-report-event="Signin_Submit"]')))
            self.find_element(By.CSS_SELECTOR, 'input[data-report-event="Signin_Submit"]').click()
        
    def toggle_ac_on(self):
        WebDriverWait(self, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[role=switch]')))
        ac_button = self.find_element(By.CSS_SELECTOR, 'button[role=switch]')
        if ac_button.get_attribute('aria-checked') == 'false':
            ac_button.click()
            WebDriverWait(self, 15).until(EC.alert_is_present())
            self._switch_to.alert.accept()
        else:
            print('AC is already on.')

    def toggle_ac_off(self):
        WebDriverWait(self, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[role=switch]')))
        ac_button = self.find_element(By.CSS_SELECTOR, 'button[role=switch]')
        if ac_button.get_attribute('aria-checked') == 'true':
            ac_button.click()
            WebDriverWait(self, 15).until(EC.alert_is_present())
            self._switch_to.alert.accept()
        else:
            print('AC is already off.')