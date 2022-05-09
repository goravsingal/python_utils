import time
from python_utils.timed_function import timedfunction_wrapper

@timedfunction_wrapper(timeout=2)
def test():
    print('In Test')
    for i in range(1, 100):
        print(f'Sleeping - {i}')
        time.sleep(1)

test()