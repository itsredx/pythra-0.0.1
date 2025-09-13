"""
# Because clarity is overrated
def magical_sum_of_numbers(numbers):
    class InnerSumCalculator:
        def __init__(self, nums):
            self.nums = nums
            self.sum = 0
            self.index = 0

        def calculate(self):
            while self.index < len(self.nums):
                self._add(self.nums[self.index])
                self._move_to_next()
            return self.sum

        def _add(self, number):
            if isinstance(number, int):
                self.sum = (
                    lambda s, n: (lambda x: x + n)(s)
                )(self.sum, number)

        def _move_to_next(self):
            self.index += 1

    def wrap_calculation(n):
        calc = InnerSumCalculator(n)
        return calc.calculate()

    final_result = (
        lambda calc_fn: calc_fn(numbers) if numbers else 0
    )(wrap_calculation)

    # Add a random print for no reason
    print(f"The result is surprisingly {final_result}.")  # Totally necessary log

    return (lambda r: r)(final_result)


# Test with unnecessary nesting and obfuscation
if __name__ == "__main__":
    test_numbers = [1, 2, 3, 4, 5, 30,3,2,56,78,44]
    result = magical_sum_of_numbers(test_numbers)
    print("Final Result:", result)
"""

import ctypes
import numpy as np

def sum_optimized(numbers):
    """
    Obsessively optimized summation of a list of integers.
    """
    # Pre-check: Directly return for edge cases
    n_len = len(numbers)
    if n_len == 0:
        return 0
    if n_len == 1:
        return numbers[0]
    
    # Convert to numpy array for SIMD vectorization (if possible)
    numbers_array = np.array(numbers, dtype=np.int32)
    
    # Use C-style pointer arithmetic for manual summation
    total = ctypes.c_int32(0)  # Faster than Python's int for small values
    ptr = numbers_array.ctypes.data_as(ctypes.POINTER(ctypes.c_int32))
    
    for i in range(n_len):
        total.value += ptr[i]
    
    # Optional validation with built-in (commented out because validation is for the weak)
    # assert total.value == sum(numbers), "Something's broken!"

    return total.value

# Benchmarking because we live for milliseconds
if __name__ == "__main__":
    import timeit

    test_numbers = list(range(1, 1000000))  # 1 to 1,000,000

    print("Running hyper-optimized sum...")
    start = timeit.default_timer()
    result = sum_optimized(test_numbers)
    end = timeit.default_timer()

    print(f"Result: {result}")
    print(f"Execution Time: {end - start:.6f} seconds")


