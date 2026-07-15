import threading
import time

counter = 0
lock = threading.Lock()

def worker_unsafe():
    global counter
    for _ in range(100_000):
        # Split read-modify-write into explicit steps.
        # time.sleep(0) yields the GIL, letting another thread run
        # BETWEEN the read and the write.
        tmp = counter
        time.sleep(0)
        counter = tmp + 1

def worker_safe():
    global counter
    for _ in range(100_000):
        with lock:
            tmp = counter
            time.sleep(0)
            counter = tmp + 1

def run(worker_fn, label):
    global counter
    counter = 0
    threads = [threading.Thread(target=worker_fn) for _ in range(2)]
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"{label}: {counter:,} (expected 200,000, lost {200_000 - counter:,})")

run(worker_unsafe, "without lock")
run(worker_safe,   "with lock   ")
