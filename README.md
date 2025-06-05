Gemini Uploader Python Script
Based on Python, using Selenium for web clicks and PyAutoGUI image-based clicks for the native Chrome pop-up if needed, sometimes it works without needing to dismiss the native pop-up on a fresh chrome profile).

1. What the Script Does (Purpose and Overall Functionality)
The primary purpose of this Python script is to automate the process of uploading a local project's files to Google Gemini. It aims to provide Gemini with the full context of a project by:

Automated Login: Securely logging into the user's Google account to access Gemini. (Without 2-FA for now)

File Structure Analysis: Scanning a specified local project folder, identifying relevant files and their structure.

Sitemap Generation: Creating a sitemap_project_tree.xml file that contains a text representation of the project's directory tree. This file is then included in the uploads.

Batch File Uploads: Uploading all selected project files (including the generated sitemap) to Gemini in manageable batches.

Gemini UI Interaction:

Attempting to select a preferred model (e.g., "Gemini 2.5 Pro (preview)").

Interacting with the file attachment UI elements.

Sending messages to Gemini to accompany the file batches, informing it about the uploads and the sitemap.

Native Pop-up Handling: Attempting to automatically dismiss the native Chrome "Make Chrome your own" (or similar sync/profile) pop-up that can appear after a fresh login.

The script combines web automation using Selenium with GUI automation using PyAutoGUI (specifically for the native Chrome pop-up).

2. How It Works (Step-by-Step Process)
The script operates in several distinct phases:

Phase A: Setup and Configuration

Import Libraries: Essential Python libraries are imported, including os, time, subprocess, sys, dotenv (for .env files to log-in with Google without 2-FA), and various Selenium modules.

Load Environment Variables (.env):

load_dotenv() is called to load variables from a .env file located in the same directory as the script.

Crucially, this loads GEMINI_UPLOADER_EMAIL and GEMINI_UPLOADER_PASSWORD for automated login.

Optionally, TARGET_FOLDER_PATH and Chrome profile paths (Chrome profiles not working at this time) can also be set here.

Global Configurations:

TARGET_FOLDER: The root directory of the project to be uploaded.

GEMINI_URL: The URL for the Gemini web application.

File/Folder Filters: SUBFOLDERS_TO_SCAN, FOLDERS_TO_IGNORE_NAMES, FILES_TO_IGNORE_NAMES, ALLOWED_EXTENSIONS define which files are included/excluded.

SITEMAP_FILENAME: Defines the name of the generated project tree file (e.g., "sitemap_project_tree.xml").

USE_CHROME_PROFILE: A boolean to decide whether to use an existing Chrome profile or launch a fresh instance (default is False for fresh instance + auto-login).

NATIVE_POPUP_CLICKER_SCRIPT_NAME and NATIVE_POPUP_DISMISS_IMAGE: Configure the PyAutoGUI script and target image for handling the native Chrome pop-up.

UI Element Locators: XPaths for common Gemini UI elements (stop button, spinners, error messages) are defined for the wait_for_gemini_ready function.

Phase B: File Preparation

Generate File Tree (generate_file_tree_text):

This function recursively scans the TARGET_FOLDER based on SUBFOLDERS_TO_SCAN, respecting the ignore lists and allowed extensions.

It constructs a multi-line string representing the directory structure.

Save Sitemap (save_tree_as_sitemap):

The generated file tree string is saved into the SITEMAP_FILENAME (e.g., sitemap_project_tree.xml) at the root of the TARGET_FOLDER.

Collect All Files for Upload (get_all_files_to_process):

This function re-scans the project (or uses the same logic) to gather a list of all absolute file paths that match the criteria.

Crucially, it's designed to ensure that the newly created SITEMAP_FILENAME is included in this list.

Phase C: Browser Automation and Login (Selenium)

Initialize WebDriver:

webdriver-manager is used to automatically download and manage the correct ChromeDriver.

Chrome options are configured:

If USE_CHROME_PROFILE = False (default):

Standard options for a clean, fresh browser instance are set (disable extensions, no-sandbox, etc.).

Numerous options and preferences are applied to try and suppress native Chrome first-run/sync/profile pop-ups.

If USE_CHROME_PROFILE = True: Options are set to use the specified existing Chrome user data directory and profile.

The browser window is started and maximized.

Navigate to Gemini: The script opens GEMINI_URL.

Automated Login (if USE_CHROME_PROFILE is False):

The script first checks if the user might already be logged in (by looking for the Gemini prompt area).

If not, it locates and clicks the "Sign in" button on the Gemini page using click_element_robustly.

It then proceeds through the Google login flow:

Enters the GOOGLE_EMAIL (from .env) into the email field.

Clicks "Next" using click_element_robustly.

Enters the GOOGLE_PASSWORD (from .env) into the password field.

Clicks "Next" using click_element_robustly.

Handle Native Chrome Pop-up (PyAutoGUI):

After submitting login credentials, the script pauses for a few seconds (time.sleep(8)).

It then calls the call_pyautogui_image_clicker helper function. This function runs your separate click_chrome_popup.py script as a subprocess.

click_chrome_popup.py (the PyAutoGUI image-based clicker) attempts to find the image specified by NATIVE_POPUP_DISMISS_IMAGE (e.g., "use_guest_button.png") on the screen and click it. This is to dismiss the "Make Chrome your own" native browser pop-up.

The main script waits for the PyAutoGUI script to finish (or timeout).

Re-navigate and Wait for Gemini:

After the PyAutoGUI script attempt, the Selenium script explicitly re-navigates to GEMINI_URL. This is important in case the native pop-up or its dismissal shifted focus or changed the URL.

It then calls wait_for_gemini_ready to ensure the Gemini application page is fully loaded and interactive.

Phase D: Interacting with Gemini UI (Selenium)

Model Selection:

The script first attempts to read the text of the currently displayed model using Selenium.

If the desired model (e.g., "Gemini 2.5 Pro (preview)") is not already active:

It uses click_element_robustly to click the model switcher dropdown button (identified by an XPath).

It pauses briefly for the dropdown to open.

It uses click_element_robustly to click the specific "Gemini 2.5 Pro (preview)" option within the dropdown (identified by an XPath).

If the target model is already selected, or if any step in the selection process fails, it logs the outcome and continues.

File Upload Loop (Batches):

The files_to_process list is divided into batches (default size 10, configurable).

For each batch:

The script uses click_element_robustly to click the "Add/Attach" icon (plus symbol) on the Gemini page.

It pauses for the upload menu to appear.

It uses click_element_robustly to click the "Upload files" button within that menu.

It pauses for the OS file dialog to be ready (though Selenium doesn't interact with this dialog directly).

Selenium then finds the hidden <input type="file"> element on the page.

It sends the file paths for the current batch (newline-separated) directly to this input element using file_input.send_keys().

It waits for the corresponding file "chips" to appear on the Gemini page to confirm upload.

It types a message into the Gemini prompt area. This message:

For the first batch, mentions that the project structure is in the SITEMAP_FILENAME which is part of the uploads.

For intermediate batches, it's a simple "please wait" message.

For the final batch, it confirms all files have been uploaded.

It clicks the "Send" button for the message using click_element_robustly.

It then calls wait_for_gemini_ready to ensure Gemini has processed the message and the attached files for that batch before starting the next one. This is crucial for preventing the script from overwhelming Gemini.

It also tries to verify that the file chips are cleared or reduced after processing.

Phase E: Helper Functions

click_element_robustly(driver, element_or_locator, ...):

This is a key Selenium helper. It takes either a pre-found WebElement or a locator tuple (e.g., (By.XPATH, "...")).

It waits for the element to be clickable using WebDriverWait.

It attempts a standard Selenium .click().

If that click is intercepted (ElementClickInterceptedException), it attempts a JavaScript click (driver.execute_script("arguments[0].click();", ...)), after ensuring the element is scrolled into view.

Includes small pauses after successful clicks.

wait_for_gemini_ready(driver, prompt_selector_css, ...):

This function polls the Gemini page to determine if it's ready for the next interaction.

It checks for:

The absence of a "Stop generating" button.

The absence of general loading spinners.

The absence of specific error messages (like "Something went wrong").

The absence of a persistent "Just a sec..." message.

The main prompt input area being clickable.

It has a configurable timeout and logs its progress.

call_pyautogui_image_clicker(image_filename_to_click, ...):

This function is responsible for running the click_chrome_popup.py (image-based PyAutoGUI) script as a subprocess. It passes the target image filename. It is used specifically for the native Chrome pop-up.

3. How to Edit for Different Users/Projects
Here's how a new user can adapt the script:

Essential Setup (Must Do):

.env File:

Create a file named .env in the same directory as the main Python script.

Add your Google credentials:

GEMINI_UPLOADER_EMAIL="your_google_email@example.com"
GEMINI_UPLOADER_PASSWORD="your_google_password_or_app_password"

(If you use 2-Factor Authentication, you'll likely need to generate an "App Password" for your Google account and use that here.)

TARGET_FOLDER (Project Path):

The easiest way is to add it to your .env file:

TARGET_FOLDER_PATH="C:\\path\\to\\your\\project" 

(Use double backslashes \\ or forward slashes / for paths in the .env file, especially on Windows).

Alternatively, directly edit this line in the Python script (at the top):

TARGET_FOLDER = os.environ.get("TARGET_FOLDER_PATH") or r"C:\Your\Default\Path\Here" 

Replace r"C:\Your\Default\Path\Here" with the absolute path to the project you want to upload. The r"" makes it a raw string, good for Windows paths.

Native Chrome Pop-up Image (NATIVE_POPUP_DISMISS_IMAGE):

The script attempts to dismiss the "Make Chrome your own" pop-up using PyAutoGUI.

You must take a screenshot of the button you want to click on that pop-up (e.g., the "Use Chrome without an account" or "No thanks" button). (Provided in this repository, may need to update if google changes the working or the pop-up.)

Save this image as a .png file (use_guest_button.png) in the same directory as the main Python script.

Update this line in the script if your image filename is different:

NATIVE_POPUP_DISMISS_IMAGE = "your_button_image_name.png" 

Install Libraries: Ensure all required Python libraries are installed. Open a terminal/PowerShell and run:

pip install selenium webdriver-manager python-dotenv pyautogui Pillow

(Pillow is needed by PyAutoGUI for image recognition).

File Scanning and Filtering (Customize as Needed):

SUBFOLDERS_TO_SCAN:

SUBFOLDERS_TO_SCAN = ["public", "home", etc.]

Edit this list to specify which subdirectories within your TARGET_FOLDER should be scanned. An empty string "" means the root of TARGET_FOLDER itself will be scanned.

FOLDERS_TO_IGNORE_NAMES:

FOLDERS_TO_IGNORE_NAMES = [".git", "node_modules", "__pycache__", ".venv", "venv"]

Add or remove folder names that should be completely skipped during the scan (e.g., version control folders, dependency folders).

FILES_TO_IGNORE_NAMES:

FILES_TO_IGNORE_NAMES = [".gitignore", ".env"]

Add or remove specific filenames that should be ignored.

ALLOWED_EXTENSIONS:

ALLOWED_EXTENSIONS = ['.txt', '.md', '.py', '.js', '.html', '.css', '.xml' ...] # Shortened for brevity

Modify this list to control which file types are included in the upload. Ensure .xml is present if you want the generated sitemap to be uploaded.

SITEMAP_FILENAME:

SITEMAP_FILENAME = "sitemap_project_tree.xml"

You can change the name of the generated project tree file if desired.

Batch Size for File Uploads:

Locate this line within the main() function, inside the file upload loop section:

file_batches_list = list(batch_files(files_to_process, 10)) 

Change the number 10 to your desired batch size. (Gemini currently only allows for 10 files to be uploaded per message sent.)

Smaller batch size (e.g., 5): More messages sent to Gemini, potentially slower overall, but might be gentler on Gemini's processing for each step.

Using an Existing Chrome Profile (Optional, USE_CHROME_PROFILE):

If you prefer to use an existing Chrome profile where you are already logged in and have handled first-run pop-ups:

Set USE_CHROME_PROFILE = True in the script. (Still working on a workaround to get this working)

Update CHROME_USER_DATA_DIR and CHROME_PROFILE_DIRECTORY to point to your specific Chrome profile path. You can find your Chrome profile path by typing chrome://version in Chrome's address bar.

USE_CHROME_PROFILE = True
CHROME_USER_DATA_DIR = r"C:\Users\YourUserName\AppData\Local\Google\Chrome\User Data" 
CHROME_PROFILE_DIRECTORY = "Profile 1" # Or "Default", "Profile 2", etc.

(Using the .env file for these paths is also an option if os.environ.get is used for them in the script).

When USE_CHROME_PROFILE is True, the automated login and native pop-up clicker steps are skipped.

Advanced: PyAutoGUI Confidence/Attempts (for Native Pop-up):

If the image-based click for the native Chrome pop-up isn't working reliably (either not finding the image or clicking the wrong thing), you can adjust parameters in the call_pyautogui_image_clicker function call within main():

if not call_pyautogui_image_clicker(NATIVE_POPUP_DISMISS_IMAGE, confidence=0.75, attempts=5, timeout_subproc=25):
    # ...

confidence: A value between 0.0 and 1.0. Lower values (e.g., 0.7) are more lenient in image matching but risk false positives. Higher values (e.g., 0.9) are stricter. Default in the call is 0.75.

attempts: How many times the PyAutoGUI script will look for the image. Default in the call is 5.

Advanced: Selenium Locators and Waits:

If Google significantly changes the Gemini web application's UI, the Selenium locators (XPaths and CSS selectors) used to find buttons, input fields, etc., might break. These are mostly at the top of the script (e.g., GEMINI_STOP_GENERATING_XPATH) or within the main() function logic for specific elements. Updating these requires inspecting the new page structure using browser developer tools.

Similarly, time.sleep() values or WebDriverWait timeouts might need adjustment if the page loads slower or faster on different systems/networks.

4. Prerequisites for New Users
Python: Python 3.7+ installed.

Google Chrome: The Chrome browser must be installed.

Python Libraries:

pip install selenium webdriver-manager python-dotenv pyautogui Pillow

.env File: Created in the script's directory with GEMINI_UPLOADER_EMAIL and GEMINI_UPLOADER_PASSWORD.

Image for Native Pop-up: A screenshot (e.g., use_guest_button.png) of the "Use Chrome without an account" button (or equivalent dismiss button for the native "Make Chrome your own" pop-up) saved in the script's directory. The NATIVE_POPUP_DISMISS_IMAGE variable in the script must match this filename.

PyAutoGUI Screen Permissions (macOS/Linux): On some operating systems, you may need to grant accessibility permissions to your terminal or Python environment for PyAutoGUI to control the mouse and see the screen.

---------------------------------------------------------------------------------------------------------------------------

This script offers a powerful way to automate the submission of entire projects to Google Gemini. By combining Selenium for web interactions and PyAutoGUI for handling the native Chrome pop-up, it navigates several complexities of modern web automation. Users can adapt it by primarily modifying the configuration variables at the top of the script and ensuring their .env file and necessary PyAutoGUI image are correctly set up. Understanding the flow and the role of each component will help in troubleshooting and customizing it further.# Gemini.ai-Auto-File-uploader
Automatically uploads files for you if you have a large project to upload (from local machine) to Gemini.google.com/app (Doesn't currently work on chrome profiles, working on a workaround for that.)
