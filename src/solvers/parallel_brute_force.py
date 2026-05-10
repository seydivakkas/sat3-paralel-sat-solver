"""
Parallel Brute Force SAT Solver
================================
ThreadPoolExecutor ile paralel brute-force SAT cozucusu.
Windows uyumlulugu icin threading kullanilir.
"""

import time
import math
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Tuple, List


class ParallelBruteForceSolver:
    """Multi-thread paralel brute-force SAT cozucusu."""

    def __init__(self, cnf, num_processes: int = 4):
        self.cnf = cnf
        self.num_processes = num_processes
        self._found = threading.Event()
        self._lock = threading.Lock()
        self._solution = None
        self._solving_thread = -1
        self.stats = {
            'num_processes': num_processes,
            'combinations_tested': 0,
            'time': 0.0,
            'status': None,
            'solving_process': None
        }

    def _check_formula(self, assignment: List[int]) -> bool:
        """Tum formulun satisfied olup olmadigini kontrol eder."""
        for clause in self.cnf.clauses:
            clause_sat = False
            for literal in clause:
                var_idx = abs(literal) - 1
                val = assignment[var_idx]
                if (literal > 0 and val == 1) or (literal < 0 and val == -1):
                    clause_sat = True
                    break
            if not clause_sat:
                return False
        return True

    def _worker(self, thread_id: int, start_range: int,
                end_range: int) -> Optional[List[int]]:
        """Thread worker fonksiyonu."""
        n = self.cnf.num_vars

        for i in range(start_range, end_range):
            if self._found.is_set():
                return None

            assignment = []
            temp = i
            for _ in range(n):
                assignment.append(1 if temp & 1 else -1)
                temp >>= 1

            if self._check_formula(assignment):
                with self._lock:
                    if not self._found.is_set():
                        self._found.set()
                        self._solution = assignment
                        self._solving_thread = thread_id
                return assignment

        return None

    def solve(self, timeout: float = 300.0) -> Tuple[str, Optional[Dict[int, bool]]]:
        """Paralel brute force ile SAT problemini cozer."""
        n = self.cnf.num_vars
        total = 2 ** n
        chunk_size = math.ceil(total / self.num_processes)

        self._found.clear()
        self._solution = None

        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=self.num_processes) as executor:
            futures = {}
            for p in range(self.num_processes):
                s = p * chunk_size
                e = min((p + 1) * chunk_size, total)
                if s >= total:
                    break
                future = executor.submit(self._worker, p, s, e)
                futures[future] = p

            for future in as_completed(futures, timeout=timeout):
                try:
                    result = future.result(timeout=1)
                except Exception:
                    continue

        elapsed = time.perf_counter() - start
        self.stats['time'] = elapsed
        self.stats['combinations_tested'] = total

        if self._solution is not None:
            self.stats['status'] = 'SAT'
            self.stats['solving_process'] = self._solving_thread
            model = {}
            for idx, val in enumerate(self._solution):
                model[idx + 1] = (val == 1)
            return 'SAT', model
        else:
            self.stats['status'] = 'UNSAT'
            return 'UNSAT', None

    def get_stats(self) -> dict:
        return self.stats.copy()
