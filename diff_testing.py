from difference import compare_files

def multi_level():
    compare_files("Multilevel1")
    compare_files("Multilevel2")
    compare_files("Multilevel3")

def mutex():
    compare_files("Mutex1")
    compare_files("Mutex2")

def semaphore():
    compare_files("Semaphore1")
    compare_files("Semaphore2")
    compare_files("Semaphore3")

def priority():
    mutex()
    semaphore()

def simple_rr():
    compare_files("RR1")
    compare_files("RR2")

def complex_rr():
    compare_files("MultipleMutexes")
    compare_files("MultipleSemaphores")
    compare_files("MutexRR1")
    compare_files("MutexRR2")
    compare_files("SemaphoreRR1")
    compare_files("SemaphoreRR2")

def rr():
    simple_rr()
    complex_rr()

if __name__ == "__main__":
    simple_rr()