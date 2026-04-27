import os
import sys
import json
import time
import random
import requests
from datetime import datetime, timedelta
from DrissionPage import ChromiumPage, ChromiumOptions

# ==========================================
# 🍪 GET COOKIES FROM GITHUB ACTION INPUT
# ==========================================
cookies_env = os.environ.get("TWITTER_COOKIES", "").strip()

if not cookies_env:
    print("🛑 ERROR: Cookies nahi mili! GitHub Action chalate waqt 'Twitter Cookies' box mein JSON paste karein.")
    sys.exit(1)

try:
    cookies_env = cookies_env.replace("True", "true").replace("False", "false").replace("'", '"')
    STATIC_COOKIES = json.loads(cookies_env)
except Exception as e:
    print(f"🛑 ERROR: Cookies ka format ghalat hai. Please valid JSON paste karein. Details: {e}")
    sys.exit(1)

# ==========================================
# 📝 DYNAMIC TEXT GENERATOR (Project 1 Architecture)
# ==========================================
# Aapke purane messages fallback ke tor par save hain
default_messages = [
    "RCB vs GT live match HD mein dekhne ke liye bio link check karein! 🏏🔥",
    "Don't miss the Kohli vs Gill battle today! Watch live stream link in my bio. 🚀",
    "IPL 2026 Live: RCB vs GT ad-free streaming available now. Check profile bio! 👇",
    "Chinnaswamy mein runs ki barish! Catch every ball live. Link in bio! 🦅"
]

titles_str = os.environ.get("TITLES") or ",,".join(default_messages)
titles = [t.strip() for t in titles_str.split(",,") if t.strip()]
hashtags_str = os.environ.get("HASHTAGS") or "#RCBvGT #ViratKohli #IPL2026 ,, #IPL #LiveCricket"
hashtags = [h.strip() for h in hashtags_str.split(",,") if h.strip()]

def get_dynamic_message():
    t = random.choice(titles)
    h = random.choice(hashtags) 
    return f"{t}\n\n{h}"

# ==========================================
# 📥 DOWNLOAD IMAGES FROM GITHUB
# ==========================================
def download_latest_images(count=3):
    image_prefix = os.environ.get("IMAGE_PREFIX", "").strip()
    print(f"🔍 GitHub se top {count} latest images dhoond rahe hain (Prefix: '{image_prefix}')...")
    
    # Apna Release API URL yahan dalein (Project 1 wala use kiya hai)
    api_url = "https://api.github.com/repos/siddu5991079-ai/twitter-images-daddy-jajaja-3/releases/latest"
    github_token = os.environ.get('GITHUB_TOKEN')
    headers = {}
    if github_token:
        headers['Authorization'] = f"token {github_token}"
    
    downloaded_paths = []
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            assets = data.get("assets", [])
            
            if image_prefix:
                assets = [a for a in assets if a["name"].startswith(image_prefix)]
            
            assets.sort(key=lambda x: x["created_at"], reverse=True)
            latest_assets = assets[:count]
            
            for i, asset in enumerate(latest_assets):
                download_url = asset["browser_download_url"]
                image_name = f"latest_dynamic_image_{i+1}.png"
                
                print(f"📥 Download shuru ({i+1}/{len(latest_assets)}): {asset['name']}")
                img_data = requests.get(download_url, headers=headers).content
                with open(image_name, 'wb') as f:
                    f.write(img_data)
                
                downloaded_paths.append(os.path.abspath(image_name))
            return downloaded_paths
        else:
            print(f"❌ GitHub API Error: Code {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Image download fail: {e}")
        return []

# ==========================================
# 🔑 TWITTER LOGIN
# ==========================================
def initial_login(page):
    print("🌐 Twitter (X) par ja rahe hain aur cookies set kar rahe hain...")
    page.get("https://x.com/404") 
    time.sleep(3)

    for cookie in STATIC_COOKIES:
        if 'twitter.com' in cookie.get('domain', '') or 'x.com' in cookie.get('domain', ''):
            page.set.cookies({
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie['domain'],
                'path': cookie.get('path', '/')
            })

    page.get("https://x.com/home")
    time.sleep(5)
    
    if "login" in page.url.lower():
        print("❌ Login Failed! Cookies expire ho chuki hain.")
        return False
    
    print("✅ Login Successful! Browser ready hai.")
    return True

# ==========================================
# 🐦 USER'S EXACT TWITTER POSTING LOGIC
# ==========================================
def run_single_post_cycle(page, loop_counter):
    print("\n--- New Automation Cycle Started ---")
    try:
        # EXACTLY 4 IMAGES LOGIC: 3 from GitHub + 1 Static (1.png)
        dynamic_image_paths = download_latest_images(count=3)
        static_image_path = os.path.abspath("1.png")
        
        final_images_list = []
        final_images_list.extend(dynamic_image_paths)
        if os.path.exists(static_image_path):
            final_images_list.append(static_image_path)
            
        final_images_list = final_images_list[:4] # Ensure max 4
        
        if len(final_images_list) < 1:
            print("❌ Koi image nahi mili. Cycle skip!")
            return "general_error"

        print(f"🔄 Preparing to upload {len(final_images_list)} total images to Twitter.")
        
        # --- Aapka original Twitter Logic yahan se shuru ---
        page.get('https://x.com/home')
        time.sleep(random.randint(6, 10))
        
        side_post_btn = page.ele('xpath://a[@aria-label="Post"]')
        if side_post_btn:
            side_post_btn.click()
            time.sleep(3)
        
        file_input = page.ele('xpath://input[@type="file"]')
        if file_input:
            print(f"Uploading {len(final_images_list)} combined images...")
            file_input.input(final_images_list)
            
            dynamic_wait = 4 + (len(final_images_list) * 2) 
            time.sleep(dynamic_wait)
            
        post_box = page.ele('xpath://div[@aria-label="Post text"]')
        if post_box:
            text_to_post = get_dynamic_message()
            post_box.input(text_to_post)
            
            time.sleep(6)
            post_btn = page.ele('xpath://button[@data-testid="tweetButton"]')
            if post_btn:
                post_btn.click(by_js=True)
                print(f"✅ BINGO! Multi-Image Post #{loop_counter} Successful.")
                time.sleep(8) # Extra wait after post
            else:
                print("❌ Post button not found.")
        else:
            print("❌ Post text box not found.")

        # Cleanup temporary downloaded images
        print("🧹 Running cleanup protocol...")
        for img_path in dynamic_image_paths: 
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
            except:
                pass
                
        return "success"

    except Exception as e:
        print(f"⚠️ Browser Automation Error: {e}")
        return "general_error"

# ==========================================
# 🔄 MAIN INFINITE LOOP (Project 1 Architecture)
# ==========================================
if __name__ == "__main__":
    start_time = datetime.now()
    max_duration = timedelta(hours=5, minutes=50) 
    
    print("🚀 Twitter Script Start... Browser khul raha hai...")
    co = ChromiumOptions()
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--window-size=1920,1080')
    co.set_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    co.set_argument('--disable-notifications') 
    
    page = ChromiumPage(co)
    
    if not initial_login(page):
        page.quit()
        sys.exit(1)

    loop_counter = 1
    
    try:
        while True:
            current_time = datetime.now()
            elapsed_time = current_time - start_time
            
            if elapsed_time >= max_duration:
                print(f"\n⏳ 5 Ghante aur 50 Minute poore ho gaye. Graceful shutdown shuru...")
                break 
                
            print(f"\n{'='*50}")
            print(f"🔄 POST CYCLE NUMBER: {loop_counter}")
            print(f"{'='*50}")
            
            run_single_post_cycle(page, loop_counter)
            
            wait_minutes = random.randint(15, 20)
            print(f"⏳ Waiting for {wait_minutes} minutes before the next cycle...")
            time.sleep(wait_minutes * 60)
            
            loop_counter += 1
            
    finally:
        print("\nBrowser permanently band kar rahe hain...")
        page.quit()
        os.system("pkill chrome")
        print("✅ Script successfully ruk gayi.")
