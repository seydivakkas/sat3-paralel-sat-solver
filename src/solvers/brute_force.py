"""
Brute Force SAT Solver (Seri)
=============================
Tüm 2^n olası truth assignment'ları deneyerek SAT problemini çözer.
"""

import time
from typing import Optional, Dict, Tuple, List


class BruteForceSolver:
    """Seri (tek thread) brute-force SAT çözücüsü."""

    def __init__(self, cnf):
        self.cnf = cnf
        self.stats = {
            'combinations_tested': 0,
            'time': 0.0,
            'status': None
        }

    def _check_clause(self, clause: List[int],
                      assignment: List[int]) -> bool:
        """Tek bir clause'un satisfied olup olmadığını kontrol eder."""
        for literal in clause:
            var_idx = abs(literal) - 1
            val = assignment[var_idx]
            if (literal > 0 and val == 1) or (literal < 0 and val == -1):
                return True
        return False

    def _check_formula(self, assignment: List[int]) -> bool:
        """Tüm formülün satisfied olup olmadığını kontrol eder."""
        for clause in self.cnf.clauses:
            if not self._check_clause(clause, assignment):
                return False
        return True

    def _int_to_assignment(self, num: int, n_vars: int) -> List[int]:
        """Tamsayıyı boolean assignment'a çevirir.
        Örnek: 5 (101) -> [1, -1, 1] (x1=T, x2=F, x3=T)
        """
        assignment = []
        for j in range(n_vars):
            if (num >> j) & 1:
                assignment.append(1)
            else:
                assignment.append(-1)
        return assignment

    def solve(self, timeout: float = 300.0,
              progress_interval: int = 100000) -> Tuple[str, Optional[Dict[int, bool]]]:
        """
        Brute force ile SAT problemini çözer.

        Args:
            timeout: Maksimum çalışma süresi (saniye)
            progress_interval: İlerleme gösterge aralığı

        Returns:
            (status, model): ('SAT', {x1: True, ...}) veya ('UNSAT', None)
        """
        n = self.cnf.num_vars
        total = 2 ** n
        start = time.perf_counter()

        for i in range(total):
            # Timeout kontrolü
            elapsed = time.perf_counter() - start
            if elapsed > timeout:
                self.stats['time'] = elapsed
                self.stats['combinations_tested'] = i
                self.stats['status'] = 'TIMEOUT'
                return 'TIMEOUT', None

            assignment = self._int_to_assignment(i, n)

            if self._check_formula(assignment):
                elapsed = time.perf_counter() - start
                self.stats['time'] = elapsed
                self.stats['combinations_tested'] = i + 1
                self.stats['status'] = 'SAT'

                # Model oluştur: {1: True, 2: False, ...}
                model = {}
                for idx, val in enumerate(assignment):
                    model[idx + 1] = (val == 1)
                return 'SAT', model

        elapsed = time.perf_counter() - start
        self.stats['time'] = elapsed
        self.stats['combinations_tested'] = total
        self.stats['status'] = 'UNSAT'
        return 'UNSAT', None

    def get_stats(self) -> dict:
        """İstatistikleri döndürür."""
        return self.stats.copy()
