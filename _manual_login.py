import sys, time
sys.path.insert(0, ".")
from rb_upload import get_driver

driver = get_driver()
driver.get("https://www.redbubble.com/portfolio/images/new")
print("opened, waiting for manual login/verification (up to 10 min)...", flush=True)

for i in range(120):
    time.sleep(5)
    url = driver.current_url
    try:
        title = driver.title
    except Exception:
        title = "?"
    print(f"[{i*5}s] url={url} title={title}", flush=True)
    if "portfolio/images/new" in url and "login" not in url.lower():
        # try to detect the upload form field as success signal
        try:
            driver.find_element("css selector", "#work_title_en")
            print("SUCCESS: form field found, logged in and past Cloudflare", flush=True)
            break
        except Exception:
            pass

print("done, leaving browser open for now", flush=True)
