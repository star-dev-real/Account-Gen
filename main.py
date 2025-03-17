import aiohttp
import asyncio
import random
import string
import json
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Characters for random password generation
chars = string.ascii_letters + string.digits + '!@#$%&*()'
random.seed()

# URLs
account_url = 'https://petstore.octoperf.com/actions/Account.action?newAccountForm='
post_url = 'https://petstore.octoperf.com/actions/Account.action'

# Semaphore to limit concurrent requests
semaphore = asyncio.Semaphore(10)  # Reduced concurrency

# Retry logic configuration
MAX_RETRIES = 5

# Rotating User-Agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

async def get_csrf_tokens(session):
    """Fetch CSRF tokens from the account creation page."""
    try:
        async with session.get(account_url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            source_page = soup.find('input', {'name': '_sourcePage'})['value']
            fp = soup.find('input', {'name': '__fp'})['value']
            return source_page, fp
    except Exception as e:
        logging.error(f"Failed to fetch CSRF tokens: {e}")
        return None, None

async def create_account(session, username, password, csrf_tokens):
    """Send a POST request to create an account."""
    data = {
        "username": username,
        "password": password,
        "repeatedPassword": password,
        "account.firstName": username + "abcd",
        "account.lastName": username + "dcba",
        "account.email": f"{username}@example.com",
        "account.phone": "123456789",
        "account.address1": "24 Address Road",
        "account.address2": "",
        "account.city": "London",
        "account.state": "Texas",
        "account.zip": "12345",
        "account.country": "America",
        "account.languagePreference": "english",
        "account.favouriteCategoryId": "FISH",
        "newAccount": "Save Account Information",
        "_sourcePage": csrf_tokens[0],
        "__fp": csrf_tokens[1],
    }

    headers = {
        "User-Agent": random.choice(user_agents),
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": account_url,
    }

    for attempt in range(MAX_RETRIES):
        try:
            async with session.post(post_url, data=data, headers=headers, allow_redirects=False) as response:
                if response.status == 302:
                    logging.info(f"Account created successfully: {username}:{password}")
                    with open('creds.txt', 'a') as f:
                        f.write(f"{username}:{password}\n")
                    break
                else:
                    response_text = await response.text()
                    logging.warning(f"Failed to create account: {username}:{password}. Status: {response.status}. Response: {response_text}")
                    if response.status == 429:  # Too Many Requests
                        await asyncio.sleep(10)  # Wait longer if rate-limited
        except Exception as e:
            logging.error(f"Request failed for {username}:{password}. Error: {e}")
            if attempt == MAX_RETRIES - 1:
                logging.error(f"Max retries reached for {username}:{password}")

async def worker(session, username):
    async with semaphore:
        # Append a random string to the username to ensure uniqueness
        unique_username = f"{username}_{random.randint(1000, 9999)}"
        password = ''.join(random.choices(chars, k=8))
        csrf_tokens = await get_csrf_tokens(session)
        if csrf_tokens[0] and csrf_tokens[1]:
            await create_account(session, unique_username, password, csrf_tokens)
        await asyncio.sleep(1)  # Add a delay between requests
        
async def main():
    """Main function to run the script."""
    try:
        with open('names.json') as f:
            names = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load names.json: {e}")
        return

    async with aiohttp.ClientSession() as session:
        tasks = []
        for name in names:
            task = asyncio.create_task(worker(session, name))
            tasks.append(task)
        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())