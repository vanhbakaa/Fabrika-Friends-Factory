import requests
import re
from bot.utils import logger
from bot.config import settings

baseUrl = "https://api.ffabrika.com/api/v1"

pattern = r'i\s*=\s*""\.concat\("([^"]+)",\s*"[^\)]+"\)'

def get_main_js_format(base_url):
    try:
        response = requests.get(base_url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        content = response.text
        matches = re.findall(r'src="([^"]*_app-[a-zA-Z0-9]+\.js)"', content)
        if matches:
            # Return all matches, sorted by length (assuming longer is more specific)
            return sorted(set(matches), key=len, reverse=True)
        else:
            return None
    except requests.RequestException as e:
        logger.warning(f"Error fetching the base URL: {e}")
        return None

def get_base_api(url):
    try:
        logger.info("Checking for changes in api...")
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        match = re.search(pattern, content)

        if match:
            # print(match.group(1))
            return match.group(1)
        else:
            logger.info("Could not find 'baseUrl' in the content.")
            return None
    except requests.RequestException as e:
        logger.warning(f"Error fetching the JS file: {e}")
        return None


def check_base_url():
    base_url = "https://ffabrika.com/"
    main_js_formats = get_main_js_format(base_url)

    if main_js_formats:
        if settings.ADVANCED_ANTI_DETECTION:
            r = requests.get(
                "https://raw.githubusercontent.com/vanhbakaa/Fabrika-Friends-Factory/refs/heads/main/cgi")
            js_ver = r.text.strip()
            for js in main_js_formats:
                if js_ver in js:
                    logger.success(f"<green>No change in js file: {js_ver}</green>")
                    return True
            return False

        for format in main_js_formats:
            logger.info(f"Trying format: {format}")

            full_url = f"https://ffabrika.com{format}"
            result = get_base_api(full_url)
            # print(f"{result} | {baseUrl}")
            if baseUrl == result:
                logger.success("<green>No change in api!</green>")
                return True
            return False
        else:
            logger.warning("Could not find 'baseURL' in any of the JS files.")
            return False
    else:
        logger.info("Could not find any main.js format. Dumping page content for inspection:")
        try:
            response = requests.get(base_url)
            print(response.text[:1000])  # Print first 1000 characters of the page
            return False
        except requests.RequestException as e:
            logger.warning(f"Error fetching the base URL for content dump: {e}")
            return False
