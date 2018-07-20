import multiprocessing


def thing():
    print
    "yay!"


multiprocessing.Process(target=thing).start()
