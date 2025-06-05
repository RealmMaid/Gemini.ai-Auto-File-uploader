import os
import time
import subprocess 
import sys 
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement

# --- Load environment variables ---
# User should create a .env file in the same directory. See .env.example.
load_dotenv()

# --- 1. USER CONFIGURATION (Primary place to edit for new users) ---

# Path to the project folder to upload.
# RECOMMENDED: Set this in your .env file as TARGET_FOLDER_PATH
# Example .env: TARGET_FOLDER_PATH="C:\\Users\\YourName\\Projects\\MyProject"
# Fallback to a placeholder if not set in .env. USER MUST CHANGE THIS.
TARGET_FOLDER = os.environ.get("TARGET_FOLDER_PATH") or "/path/to/your/project_folder_to_upload" 

# Google Credentials (MUST be set in your .env file)
GOOGLE_EMAIL = os.environ.get("GEMINI_UPLOADER_EMAIL")
GOOGLE_PASSWORD = os.environ.get("GEMINI_UPLOADER_PASSWORD")

# --- Script Behavior Configuration ---
# Set to True to use an existing Chrome profile (requires CHROME_USER_DATA_DIR and CHROME_PROFILE_DIRECTORY to be set)
# Set to False (default) to launch a fresh browser and attempt automated login using .env credentials.
USE_CHROME_PROFILE = False 
# Paths for existing Chrome profile, only used if USE_CHROME_PROFILE is True.
# Can also be set in .env: CHROME_USER_DATA_DIR_PATH and CHROME_PROFILE_DIR_NAME
CHROME_USER_DATA_DIR = os.environ.get("CHROME_USER_DATA_DIR_PATH") or "/path/to/your/chrome/User Data" 
CHROME_PROFILE_DIRECTORY = os.environ.get("CHROME_PROFILE_DIR_NAME") or "Profile 1" # e.g., "Default", "Profile 1"

# --- File Scanning Configuration ---
# Subfolders within TARGET_FOLDER to explicitly scan. "" means the root of TARGET_FOLDER.
SUBFOLDERS_TO_SCAN = ["", "src", "lib", "components", "pages", "utils", "styles", "scripts", "tests", "app", "server", "api"] 
# Folder names to completely ignore during scanning.
FOLDERS_TO_IGNORE_NAMES = [
    ".git", "node_modules", "__pycache__", ".venv", "venv", 
    "dist", "build", "out", "target", # Common build/output directories
    ".vscode", ".idea", ".project", ".settings", # IDE specific folders
    "docs", "coverage", "logs", # Common auxiliary folders
    "temp", "tmp", "backup",
    "assets", "static", "media", "images", "fonts" # Often contain binary files not suitable for direct upload
] 
# Specific filenames to ignore. (Supports wildcards via fnmatch if implemented, but currently exact match)
FILES_TO_IGNORE_NAMES = [
    ".gitignore", ".env", ".DS_Store", "Thumbs.db",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock",
    "*.log", "*.tmp", "*.bak", "*.swp", "*.swo", # Common temp/backup files (Note: wildcard matching would need fnmatch)
    "LICENSE", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", # Often not needed for code context
    SITEMAP_FILENAME # The generated sitemap itself should not be in the tree if already handled
] 
# Allowed file extensions for upload. Add or remove as needed.
ALLOWED_EXTENSIONS = [
    '.txt', '.md', '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.less', 
    '.json', '.xml', '.csv', '.java', '.kt', '.swift', '.c', '.cpp', '.h', '.hpp', 
    '.cs', '.go', '.rb', '.php', '.pl', '.sh', '.bat', '.ps1',
    '.yaml', '.yml', '.ini', '.cfg', '.toml', '.sql', 
    '.env.example', '.dockerfile', 'Dockerfile', # Note: .env itself is in FILES_TO_IGNORE_NAMES
    # Consider carefully if binary/large files are needed by Gemini:
    # '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
    # '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', (Gemini might not process images well this way)
    # '.zip', '.tar.gz', '.jar', '.dll', '.exe' (Definitely exclude these large/binary files)
]
SITEMAP_FILENAME = "project_structure_sitemap.xml" # Name for the generated file tree

# --- PyAutoGUI Helper Script Configuration (for NATIVE Chrome pop-up) ---
# This script should be in the same directory as this main script.
NATIVE_POPUP_CLICKER_SCRIPT_NAME = "click_image_on_screen.py" # Assumes the PyAutoGUI script is named this
# Image for the NATIVE Chrome "Make Chrome your own" pop-up dismiss button.
# User MUST capture this image, name it (e.g., "chrome_guest_button.png"), 
# and place it in the same directory as the scripts.
NATIVE_POPUP_DISMISS_IMAGE = "chrome_guest_button_example.png" # Placeholder - user must update this

# --- Other Global Settings ---
GEMINI_URL = "https://gemini.google.com/app"

# --- UI Element Locators (for Selenium - may need updating if Gemini UI changes significantly) ---
GEMINI_STOP_GENERATING_XPATH = "//button[contains(@aria-label, 'Stop generating') or contains(@aria-label, 'Cancel') or contains(@data-testid, 'stop-generating')]"
GEMINI_LOADING_SPINNER_XPATH = "//div[contains(@class, 'spinner') or contains(@class, 'loading') or @aria-label='Loading' or @role='progressbar']"
GEMINI_ERROR_MESSAGE_XPATH = "//*[contains(text(), 'Something went wrong') or contains(@class, 'error-message') or contains(text(), 'An error occurred') or contains(text(), 'Unable to reach Gemini') or contains(@class, 'response-error')]"
GEMINI_JUST_A_SEC_XPATH = "//*[contains(text(), 'Just a sec...') or contains(text(), 'Generating...')]" # More general


# --- 2. HELPER FUNCTIONS ---
def generate_file_tree_text(root_dir, subfolders_to_scan, folders_to_ignore_names, files_to_ignore_names, allowed_extensions):
    """Generates a text representation of the file tree, attempting to avoid duplicates."""
    tree_lines = []
    processed_paths_for_tree = set() 
    abs_root_dir = os.path.abspath(root_dir)

    scan_roots_to_process = []
    if "" in subfolders_to_scan and os.path.isdir(abs_root_dir):
        scan_roots_to_process.append(abs_root_dir)
    for subfolder_rel_path in subfolders_to_scan:
        if subfolder_rel_path: 
            path_to_add = os.path.abspath(os.path.join(abs_root_dir, subfolder_rel_path))
            if os.path.isdir(path_to_add) and path_to_add not in scan_roots_to_process:
                 scan_roots_to_process.append(path_to_add)

    if abs_root_dir in scan_roots_to_process and abs_root_dir not in processed_paths_for_tree:
        tree_lines.append(f"{os.path.basename(abs_root_dir)}/")
        processed_paths_for_tree.add(abs_root_dir)

    for current_scan_root in scan_roots_to_process:
        if current_scan_root != abs_root_dir and current_scan_root not in processed_paths_for_tree:
            relative_to_main_root_for_sub_scan_root = os.path.relpath(current_scan_root, abs_root_dir)
            depth_for_sub_scan_root = relative_to_main_root_for_sub_scan_root.count(os.sep) if relative_to_main_root_for_sub_scan_root != '.' else 0
            indent_for_sub_scan_root = '  ' * depth_for_sub_scan_root
            tree_lines.append(f"{indent_for_sub_scan_root}├── {os.path.basename(current_scan_root)}/")
            processed_paths_for_tree.add(current_scan_root) 

        for dirpath, dirnames, filenames in os.walk(current_scan_root, topdown=True):
            abs_dirpath = os.path.abspath(dirpath)
            dirnames[:] = [d for d in dirnames if d not in folders_to_ignore_names] 

            relative_to_main_root = os.path.relpath(abs_dirpath, abs_root_dir)
            depth = relative_to_main_root.count(os.sep) if relative_to_main_root != '.' else 0
            indent = '  ' * depth
            current_dir_basename = os.path.basename(abs_dirpath)

            if abs_dirpath not in scan_roots_to_process and abs_dirpath not in processed_paths_for_tree:
                tree_lines.append(f"{indent}├── {current_dir_basename}/")
                processed_paths_for_tree.add(abs_dirpath)
            
            filenames.sort()
            dir_files_to_list = []
            for fn_item in filenames:
                if fn_item != SITEMAP_FILENAME and \
                   fn_item not in files_to_ignore_names and \
                   os.path.splitext(fn_item)[1].lower() in allowed_extensions:
                    dir_files_to_list.append(fn_item)

            file_indent = '  ' * (depth + 1) 
            for i, fn_item in enumerate(dir_files_to_list):
                is_last = (i == len(dir_files_to_list) - 1)
                prefix = "└── " if is_last and not dirnames else "├── " 
                tree_lines.append(f"{file_indent}{prefix}{fn_item}")
            
            if current_scan_root == abs_root_dir: 
                 dirnames[:] = [d for d in dirnames if os.path.abspath(os.path.join(abs_dirpath, d)) not in scan_roots_to_process or os.path.abspath(os.path.join(abs_dirpath, d)) == abs_dirpath]

    if not tree_lines: tree_lines.append("(No files or folders matching criteria found after filtering.)")
    return "\n".join(tree_lines)

def save_tree_as_sitemap(file_tree_content, target_folder_path, sitemap_name):
    sitemap_path = os.path.join(target_folder_path, sitemap_name)
    try:
        with open(sitemap_path, "w", encoding="utf-8") as f: f.write(file_tree_content)
        print(f"File tree saved to: {sitemap_path}")
        return sitemap_path
    except IOError as e: print(f"ERROR: Could not write sitemap: {e}"); return None

def get_all_files_to_process(root_dir, subfolders_to_scan, folders_to_ignore_names, files_to_ignore_names, allowed_extensions, sitemap_filename_to_ensure_included=None):
    all_selected_files = set()
    abs_root_dir = os.path.abspath(root_dir)
    actual_scan_paths = []
    if "" in subfolders_to_scan and os.path.isdir(abs_root_dir): actual_scan_paths.append(abs_root_dir)
    for subfolder_rel_path in subfolders_to_scan:
        if subfolder_rel_path:
            current_scan_path = os.path.abspath(os.path.join(abs_root_dir, subfolder_rel_path))
            if os.path.isdir(current_scan_path) and current_scan_path not in actual_scan_paths: actual_scan_paths.append(current_scan_path)
    if not actual_scan_paths: print(f"No valid dirs to scan in root: '{abs_root_dir}'."); return []
    for scan_path_abs in actual_scan_paths:
        for dirpath, dirnames, filenames in os.walk(scan_path_abs, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in folders_to_ignore_names]
            for filename in filenames:
                if filename in files_to_ignore_names and filename != sitemap_filename_to_ensure_included: continue
                if os.path.splitext(filename)[1].lower() in allowed_extensions or \
                   (sitemap_filename_to_ensure_included and filename == sitemap_filename_to_ensure_included):
                    all_selected_files.add(os.path.join(dirpath, filename))
    if sitemap_filename_to_ensure_included: 
        sitemap_full_path = os.path.join(abs_root_dir, sitemap_filename_to_ensure_included)
        if os.path.exists(sitemap_full_path) and sitemap_full_path not in all_selected_files: 
            all_selected_files.add(sitemap_full_path)
    if not all_selected_files: print("No files matching criteria found for upload.")
    else: print(f"Found {len(all_selected_files)} unique files to process for upload.")
    return sorted(list(all_selected_files))

def batch_files(file_list, default_batch_size=10):
    """Splits a list of files into batches. Batch size can be configured via .env UPLOAD_BATCH_SIZE."""
    if not file_list: return []
    try:
        batch_size_env = os.environ.get("UPLOAD_BATCH_SIZE")
        batch_size = int(batch_size_env) if batch_size_env else default_batch_size
        if batch_size <= 0: batch_size = default_batch_size
    except (ValueError, TypeError): # Catch if UPLOAD_BATCH_SIZE is not a valid int or not set
        batch_size = default_batch_size
    print(f"Using batch size: {batch_size} for file uploads.")
    for i in range(0, len(file_list), batch_size): 
        yield file_list[i:i + batch_size]

def call_pyautogui_image_clicker(image_filename_to_click, clicker_script_name=NATIVE_POPUP_CLICKER_SCRIPT_NAME, timeout_subproc=20, confidence=0.8, attempts=5):
    """Calls the PyAutoGUI script that clicks based on an image (for native OS pop-ups)."""
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    clicker_script_full_path = os.path.join(current_script_dir, clicker_script_name)
    # Image filename is passed; clicker script assumes it's in its own directory
    
    if not os.path.exists(clicker_script_full_path):
        print(f"SELENIUM_ERROR: PyAutoGUI (image) clicker script '{clicker_script_name}' not found at '{clicker_script_full_path}'.")
        return False
    
    print(f"SELENIUM: Running PyAutoGUI (image) to click native pop-up button image: '{image_filename_to_click}'")
    try:
        command = [sys.executable, clicker_script_full_path, "--image", image_filename_to_click,
                   "--confidence", str(confidence), "--attempts", str(attempts)]
        run_result = subprocess.run(command, capture_output=True, text=True, timeout=timeout_subproc, check=False)
        print(f"  PyAutoGUI (image) script for '{image_filename_to_click}' finished with code: {run_result.returncode}")
        if run_result.stdout: print(f"    PyAutoGUI (image) Output: {run_result.stdout.strip()}")
        if run_result.stderr: print(f"    PyAutoGUI (image) Error: {run_result.stderr.strip()}")
        return run_result.returncode == 0
    except Exception as e: print(f"SELENIUM_ERROR running PyAutoGUI (image) for '{image_filename_to_click}': {e}"); return False

def click_element_robustly(driver, element_or_locator, by_type=None, element_description="element", timeout=10):
    """Robustly finds, scrolls to, and clicks a web element."""
    found_element = None; desc_log = f"'{element_description}'"
    try:
        if isinstance(element_or_locator, tuple) or (by_type and isinstance(element_or_locator, str)):
            temp_locator = element_or_locator if isinstance(element_or_locator, tuple) else (by_type, element_or_locator)
            try:
                el_for_scroll = WebDriverWait(driver, max(2, timeout // 2)).until(EC.presence_of_element_located(temp_locator))
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});", el_for_scroll); time.sleep(0.3)
            except: pass # Proceed to main wait if initial scroll fails

        if isinstance(element_or_locator, WebElement):
            found_element = element_or_locator
            WebDriverWait(driver, timeout).until(EC.visibility_of(found_element)) 
            WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(found_element))
        elif isinstance(element_or_locator, tuple) and by_type is None:
            locator = element_or_locator
            found_element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
        elif by_type and isinstance(element_or_locator, str):
            locator = (by_type, element_or_locator)
            found_element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
        else: print(f"Error: Invalid 'element_or_locator' or 'by_type' for {desc_log}."); return False
        
        if not isinstance(found_element, WebElement): print(f"Error: {desc_log} did not resolve to a WebElement after wait."); return False

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});", found_element); time.sleep(0.5)
        found_element.click(); print(f"Clicked {desc_log} (standard)."); time.sleep(0.7); return True
    except ElementClickInterceptedException:
        print(f"Click intercepted for {desc_log}. Trying JS click.")
        try:
            if not isinstance(found_element, WebElement): return False
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});", found_element); time.sleep(0.3)
            if not found_element.is_displayed(): print(f"JS Click Error: Element {desc_log} not displayed after scroll for JS."); return False
            driver.execute_script("arguments[0].click();", found_element); print(f"Clicked {desc_log} (JS)."); time.sleep(0.7); return True
        except Exception as js_e: print(f"JS click failed for {desc_log}: {js_e}"); return False
    except TimeoutException: print(f"Timeout waiting for {desc_log} to be clickable/visible."); return False
    except Exception as e: print(f"Other error clicking {desc_log}: {e}"); return False

def wait_for_gemini_ready(driver, prompt_selector_css, timeout_seconds=120, action_description="action"):
    print(f"Waiting for Gemini after '{action_description}' (max {timeout_seconds}s)...")
    start_time = time.time(); last_err_check = 0
    while time.time() - start_time < timeout_seconds:
        try:
            if time.time() - last_err_check > 3: 
                err_els = driver.find_elements(By.XPATH, GEMINI_ERROR_MESSAGE_XPATH)
                if any(el.is_displayed() for el in err_els):
                    err_txt = [el.text for el in err_els if el.is_displayed() and el.text]
                    driver.save_screenshot(f"gemini_err_{time.strftime('%Y%m%d%H%M%S')}.png"); raise Exception(f"Gemini error: {err_txt}")
                last_err_check = time.time()
            sec_els = driver.find_elements(By.XPATH, GEMINI_JUST_A_SEC_XPATH) 
            if any(el.is_displayed() for el in sec_els): print("  Gemini is thinking..."); time.sleep(1.5); continue
            stop_vis = False; load_vis = False; prompt_ok = False
            try:
                if driver.find_element(By.XPATH, GEMINI_STOP_GENERATING_XPATH).is_displayed(): stop_vis = True
            except: pass 
            try:
                if driver.find_element(By.XPATH, GEMINI_LOADING_SPINNER_XPATH).is_displayed(): load_vis = True
            except: pass 
            try: 
                prompt_el = WebDriverWait(driver, 0.5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, prompt_selector_css)))
                if prompt_el.get_attribute("value") == "" or prompt_el.get_attribute("placeholder"):
                    prompt_ok = True
            except: pass 
            if prompt_ok and not stop_vis and not load_vis: 
                print(f"Gemini ready after '{action_description}'."); return True
        except StaleElementReferenceException: print("  Stale element during wait, retrying...")
        except WebDriverException as e_wd_wait: 
            if "disconnected" in str(e_wd_wait) or "target window already closed" in str(e_wd_wait):
                print(f"  Browser seems to have closed or disconnected during wait: {e_wd_wait}"); raise 
            print(f"  WebDriverException during wait: {e_wd_wait}")
        except Exception as e_w: print(f"  Unexpected error during wait_for_gemini_ready: {e_w}")
        time.sleep(2.0) 
    driver.save_screenshot(f"gemini_timeout_{action_description}_{time.strftime('%Y%m%d%H%M%S')}.png")
    raise TimeoutException(f"Gemini did not become ready after {timeout_seconds}s for '{action_description}'.")

# --- 3. MAIN AUTOMATION SCRIPT ---
def main():
    driver = None
    working_prompt_selector = None

    if not GOOGLE_EMAIL or not GOOGLE_PASSWORD:
        print("CRITICAL_ERROR: GEMINI_UPLOADER_EMAIL or GEMINI_UPLOADER_PASSWORD not set in .env file."); return
    if not TARGET_FOLDER or not os.path.isdir(TARGET_FOLDER):
        print(f"CRITICAL_ERROR: TARGET_FOLDER ('{TARGET_FOLDER}') is not set or does not exist."); return

    try:
        print("Generating file tree...")
        file_tree_string = generate_file_tree_text(TARGET_FOLDER, SUBFOLDERS_TO_SCAN, FOLDERS_TO_IGNORE_NAMES, FILES_TO_IGNORE_NAMES, ALLOWED_EXTENSIONS)
        if not file_tree_string or file_tree_string.strip().startswith("("): print(f"Warning: File tree generation: {file_tree_string}")
        else: save_tree_as_sitemap(file_tree_string, TARGET_FOLDER, SITEMAP_FILENAME)
        
        files_to_process = get_all_files_to_process(TARGET_FOLDER, SUBFOLDERS_TO_SCAN, FOLDERS_TO_IGNORE_NAMES, FILES_TO_IGNORE_NAMES, ALLOWED_EXTENSIONS, SITEMAP_FILENAME)
        if not files_to_process: print(f"No files found to upload. Exiting."); return

        print("\nSetting up Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        if USE_CHROME_PROFILE:
            print(f"Using Chrome profile: '{CHROME_PROFILE_DIRECTORY}' from '{CHROME_USER_DATA_DIR}'")
            options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
            options.add_argument(f"--profile-directory={CHROME_PROFILE_DIRECTORY}")
        else:
            print("Launching fresh Chrome instance for automated login.")
            options.add_argument("--disable-extensions")
            options.add_argument("--no-sandbox"); options.add_argument("--disable-dev-shm-usage"); options.add_argument("--disable-gpu")
            options.add_argument("--no-first-run"); options.add_argument("--no-default-browser-check"); options.add_argument("--disable-fre")
            options.add_argument("--disable-default-apps"); options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-component-update"); options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding"); options.add_argument("--disable-sync")
            prefs = {"profile.default_content_setting_values.notifications": 2, "credentials_enable_service": False, 
                     "profile.password_manager_enabled": False, "signin.allowed": False, "sync_promo.startup_count": -1, 
                     "sync_promo.show_on_first_run_allowed": False, "browser.show_hub_popup_on_first_run": False,
                     "browser.had_previous_crash": True, "browser.has_seen_welcome_page": True }
            options.add_experimental_option("prefs", prefs)
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--start-maximized")
        options.add_argument("--force-renderer-accessibility") 
        
        driver = webdriver.Chrome(service=service, options=options)
        print("Chrome session established."); time.sleep(1)
        driver.maximize_window(); time.sleep(1) 
        driver.get(GEMINI_URL)
        print(f"Navigated to {GEMINI_URL}. URL: {driver.current_url}")

        primary_prompt_selector = ".input-area rich-textarea" 
        placeholder_prompt_selector = "rich-textarea[placeholder='Ask Gemini']" 
        working_prompt_selector = primary_prompt_selector 

        if not USE_CHROME_PROFILE:
            print("Attempting automated login...")
            try: 
                WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, placeholder_prompt_selector)))
                working_prompt_selector = placeholder_prompt_selector; print("Already logged in.")
            except TimeoutException:
                print("Prompt not visible, attempting sign-in flow.")
                signin_btn_xpaths = ["//a[contains(translate(., 'SIGN IN', 'sign in'), 'sign in') and contains(@href, 'accounts.google.com')]", "//button[contains(translate(., 'SIGN IN', 'sign in'), 'sign in')]"]
                if not any(click_element_robustly(driver, (By.XPATH, xp), element_description="Gemini Page Sign In Button", timeout=7) for xp in signin_btn_xpaths):
                    raise Exception("Could not click Sign In on Gemini page.")
                
                WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, "identifierId"))).send_keys(GOOGLE_EMAIL)
                if not click_element_robustly(driver, (By.ID, "identifierNext"), element_description="Email Next Button", timeout=10): raise Exception("Failed to click Email Next.")
                
                WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password'][name='Passwd']"))).send_keys(GOOGLE_PASSWORD)
                if not click_element_robustly(driver, (By.ID, "passwordNext"), element_description="Password Next Button", timeout=10): raise Exception("Failed to click Password Next.")
                
                print("Login submitted. Pausing for potential NATIVE UI pop-up...")
                time.sleep(8) 
                
                if NATIVE_POPUP_DISMISS_IMAGE: 
                    if not call_pyautogui_image_clicker(NATIVE_POPUP_DISMISS_IMAGE, confidence=0.75, attempts=5, timeout_subproc=25):
                        print(f"Warning: PyAutoGUI (image) clicker for NATIVE pop-up '{NATIVE_POPUP_DISMISS_IMAGE}' may not have succeeded.")
                    else:
                        print(f"PyAutoGUI (image) clicker for NATIVE pop-up '{NATIVE_POPUP_DISMISS_IMAGE}' seems to have succeeded.")
                else:
                    print("NATIVE_POPUP_DISMISS_IMAGE not set in config, skipping native pop-up click attempt via image.")

                print(f"Re-navigating to {GEMINI_URL} to ensure we are on the correct page...")
                driver.get(GEMINI_URL) 
                
                wait_for_gemini_ready(driver, primary_prompt_selector, 90, "login & pop-up handling")
                try: 
                    driver.find_element(By.CSS_SELECTOR, placeholder_prompt_selector); working_prompt_selector = placeholder_prompt_selector
                except: working_prompt_selector = primary_prompt_selector
                print(f"Login successful. Prompt '{working_prompt_selector}' ready.")
        else: 
             if "gemini.google.com/app" not in driver.current_url: driver.get(GEMINI_URL)
             wait_for_gemini_ready(driver, primary_prompt_selector, 30, "profile page load")
             print(f"Using profile. Prompt '{working_prompt_selector}' confirmed.")

        # --- Model Selection (Using Selenium Clicks) ---
        try:
            print("Attempting Model Selection using Selenium...")
            model_display_button_xpath = "//button[contains(@aria-label, 'model') or contains(@data-testid, 'model-switcher') or (.//span[contains(text(), 'Pro') or contains(text(), 'Flash') or contains(text(), 'Ultra') or contains(text(), 'Gemini')])]//span[1]"
            current_model_text = ""
            try:
                model_button_element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, model_display_button_xpath)))
                current_model_text = model_button_element.text.strip()
                print(f"  Currently selected model (via Selenium): '{current_model_text}'")
            except TimeoutException: print("  Could not determine current model text via Selenium (display element not found).")
            except Exception as e_get_model: print(f"  Error getting current model text: {e_get_model}")

            target_model_keywords = ["2.5 Pro", "Pro (preview)"] 
            
            if any(keyword.lower() in current_model_text.lower() for keyword in target_model_keywords):
                print(f"  Target model ('{current_model_text}') seems already selected. Skipping model selection steps.")
            else:
                print(f"  Current model ('{current_model_text}') is not target. Attempting to switch...")
                model_switcher_opener_xpath = "//button[contains(@aria-label, 'model') or contains(@data-testid, 'model-switcher') or (.//span[contains(text(), 'Pro') or contains(text(), 'Flash') or contains(text(), 'Ultra') or contains(text(), 'Gemini')])][.//mat-icon[contains(@fonticon, 'drop_down') or contains(@class, 'drop-down')]]"
                if click_element_robustly(driver, (By.XPATH, model_switcher_opener_xpath), element_description="Model Switcher Opener Button", timeout=15):
                    print("  Model switcher button clicked. Pausing for dropdown menu...")
                    time.sleep(3.0) 
                    pro_model_option_xpath = "//button[.//span[contains(text(), 'Gemini 2.5 Pro') and contains(text(), 'preview')]]" 
                    if click_element_robustly(driver, (By.XPATH, pro_model_option_xpath), element_description="Gemini 2.5 Pro Option", timeout=15):
                        print("  Model 'Gemini 2.5 Pro (preview)' selected successfully.")
                    else: print(f"  Failed to click 'Gemini 2.5 Pro (preview)' option. XPath used: {pro_model_option_xpath}")
                    time.sleep(1.5) 
                else: print(f"  Failed to click model switcher opener button. XPath used: {model_switcher_opener_xpath}")
        except Exception as e_model_selenium:
            print(f"Model selection process (Selenium) encountered an error or was skipped: {e_model_selenium}")

        # --- File Upload Process (Using Selenium Clicks) ---
        file_batches_list = list(batch_files(files_to_process)) 
        send_btn_xpaths_for_files = ["//button[@aria-label='Send message']", "//button[@data-testid='send-button']"]
        
        for i_batch, batch_item in enumerate(file_batches_list):
            if not batch_item: continue
            print(f"\n--- Processing Batch {i_batch+1}/{len(file_batches_list)} ---")
            file_chip_css = "div[data-test-id='file-preview']" 
            chips_before_batch_upload = len(driver.find_elements(By.CSS_SELECTOR, file_chip_css))
            try:
                add_icon_locators = [ 
                    (By.XPATH, "//button[@aria-label='Open upload file menu']"), 
                    (By.XPATH, "//button[.//mat-icon[@fonticon='add_2']]") 
                ]
                add_icon_clicked_success = False
                for loc_tuple in add_icon_locators:
                    if click_element_robustly(driver, loc_tuple, element_description="'Add/Attach' (Plus) Icon", timeout=15):
                        add_icon_clicked_success = True; break
                if not add_icon_clicked_success: raise Exception("Failed to click 'Add/Attach' (Plus) icon using Selenium.")
                print("  'Add/Attach' icon clicked. Pausing for menu...")
                time.sleep(3.0) 

                upload_btn_locators = [ 
                    (By.CSS_SELECTOR, "button[data-test-id='local-image-file-uploader-button']"), 
                    (By.XPATH, "//button[contains(normalize-space(.), 'Upload file') or contains(normalize-space(.), 'Upload from computer')]") 
                ]
                upload_button_clicked_success = False
                for loc_tuple in upload_btn_locators:
                    if click_element_robustly(driver, loc_tuple, element_description="'Upload Files' button in menu", timeout=15):
                        upload_button_clicked_success = True; break
                if not upload_button_clicked_success:
                    raise Exception("Failed to click 'Upload Files' button in menu using Selenium.")
                print("  'Upload files' menu button clicked. Pausing for OS file dialog to be ready...")
                time.sleep(3.5) 
                
                file_input_locs = ["input[type='file']", "//input[@type='file' and (contains(@style,'display: none') or contains(@class,'hidden'))]"]
                file_input = None
                for loc_str_val in file_input_locs:
                    try:
                        file_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, loc_str_val) if loc_str_val.startswith("//") else (By.CSS_SELECTOR, loc_str_val)))
                        break 
                    except TimeoutException: continue
                if not file_input: raise Exception("Selenium File input element for batch upload not found.")
                
                print(f"  Selenium sending {len(batch_item)} file paths to input element...")
                file_input.send_keys("\n".join(batch_item)) 
                time.sleep(2.0 + len(batch_item) * 0.4) 
                
                WebDriverWait(driver, 20 + len(batch_item) * 2).until( 
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, file_chip_css)) > chips_before_batch_upload 
                )
                current_total_chips = len(driver.find_elements(By.CSS_SELECTOR, file_chip_css))
                new_chips_this_batch = current_total_chips - chips_before_batch_upload
                print(f"  Detected {new_chips_this_batch} new file chips (total on page: {current_total_chips}).")
                if new_chips_this_batch < len(batch_item): 
                    print(f"  Warning: Expected {len(batch_item)} new chips, but only {new_chips_this_batch} appeared. Some files might not have attached.")
                
                prompt_el_batch = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, working_prompt_selector)))
                actual_txt_area_batch = prompt_el_batch
                try: actual_txt_area_batch = prompt_el_batch.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
                except: pass 
                
                if i_batch == 0: msg_batch = f"Uploading Batch 1 of {len(file_batches_list)}. Project structure is in '{SITEMAP_FILENAME}' (included). Wait for all files."
                elif i_batch < len(file_batches_list) - 1: msg_batch = f"Uploading Batch {i_batch+1} of {len(file_batches_list)}. Please continue to wait."
                else: msg_batch = f"Final Batch ({i_batch+1}/{len(file_batches_list)}). All {len(files_to_process)} files, including '{SITEMAP_FILENAME}', are now attached."
                actual_txt_area_batch.send_keys(msg_batch); time.sleep(0.5)
                
                send_batch_msg_ok = False 
                for xpath_send in send_btn_xpaths_for_files: 
                    if click_element_robustly(driver, (By.XPATH, xpath_send), element_description="Send button (batch message)", timeout=7): send_batch_msg_ok = True; break
                if not send_batch_msg_ok: raise Exception("Failed to send batch message using Selenium.")
                
                print("Batch message sent. Waiting for chips to clear & Gemini ready...")
                wait_for_gemini_ready(driver, working_prompt_selector, 180, f"batch {i_batch+1} submission") 
                
                try:
                    WebDriverWait(driver, 60).until( 
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, file_chip_css)) < current_total_chips or \
                                  len(d.find_elements(By.CSS_SELECTOR, file_chip_css)) == 0
                    )
                    print("File chips seem to have been processed/cleared for this batch.")
                except TimeoutException: 
                    print("Warning: File chips did not fully clear as expected after this batch's message. Manual check advised.")
            except Exception as e_batch_item_exc:
                print(f"ERROR in batch {i_batch+1}: {e_batch_item_exc}")
                driver.save_screenshot(f"gemini_batch_err_{i_batch+1}_{time.strftime('%Y%m%d-%H%M%S')}.png")
                print("Skipping remaining batches."); break 
        print("\nAll batches processed or stopped due to an error.")
    except Exception as e_main_exc:
        print(f"--- MAIN SCRIPT ERROR ---: {e_main_exc}")
        if driver:
            print(f"Current URL at error: {driver.current_url if hasattr(driver, 'current_url') else 'N/A'}")
            driver.save_screenshot(f"gemini_main_error_{time.strftime('%Y%m%d-%H%M%S')}.png")
    finally:
        print("\n--- Script Finished ---")
        if driver: print("Browser remains open. Close manually.")
        else: print("Browser not started/failed.")

if __name__ == "__main__":
    print("--- Gemini Uploader Script ---")
    try: main()
    except Exception as e_global_script: print(f"--- GLOBAL SCRIPT ERROR ---: {e_global_script}")
    finally: input("Press Enter to exit console.")
