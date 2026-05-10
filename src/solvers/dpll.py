"""
DPLL SAT Solver
===============
Davis-Putnam-Logemann-Loveland algoritması.
Unit Propagation, Pure Literal Elimination ve Backtracking ile SAT çözer.
"""

import time
import copy
from typing import List, Dict, Optional, Set, Tuple
from collections import Counter


class DPLLSolver:
    """DPLL algoritması tabanlı SAT çözücüsü."""

    def __init__(self, cnf):
        self.cnf = cnf
        self.stats = {
            'decisions': 0,
            'unit_propagations': 0,
            'backtracks': 0,
            'time': 0.0,
            'status': None
        }

    def _simplify(self, clauses: List[List[int]],
                  literal: int) -> Optional[List[List[int]]]:
        """
        Bir literal'ı true yaparak clause listesini sadeleştirir.
        - literal içeren clause'ları kaldırır (satisfied)
        - -literal içeren clause'lardan -literal'ı çıkarır
        - Boş clause oluşursa None döndürür (conflict)
        """
        new_clauses = []
        for clause in clauses:
            if literal in clause:
                # Bu clause satisfied, atla
                continue
            neg = -literal
            if neg in clause:
                # Negatif literal'ı çıkar
                new_clause = [l for l in clause if l != neg]
                if not new_clause:
                    # Boş clause -> conflict
                    return None
                new_clauses.append(new_clause)
            else:
                new_clauses.append(clause[:])
        return new_clauses

    def _unit_propagation(self, clauses: List[List[int]],
                          assignment: Dict[int, bool]) -> Tuple[
                              Optional[List[List[int]]], Dict[int, bool]]:
        """
        Unit Propagation: Tek literal kalan clause'ları zorunlu ata.
        Tekrarla: fixed point'e ulaşana kadar.
        """
        changed = True
        while changed:
            changed = False
            for clause in clauses:
                if len(clause) == 1:
                    # Unit clause bulundu
                    lit = clause[0]
                    var = abs(lit)
                    val = lit > 0

                    if var in assignment:
                        if assignment[var] != val:
                            return None, assignment  # Conflict
                        continue

                    assignment[var] = val
                    self.stats['unit_propagations'] += 1

                    clauses = self._simplify(clauses, lit)
                    if clauses is None:
                        return None, assignment  # Conflict
                    changed = True
                    break

        return clauses, assignment

    def _pure_literal_elimination(self, clauses: List[List[int]],
                                  assignment: Dict[int, bool]) -> Tuple[
                                      List[List[int]], Dict[int, bool]]:
        """
        Pure Literal Elimination: Sadece pozitif veya negatif görünen
        literal'ları bul ve ata.
        """
        literal_polarity: Dict[int, Set[bool]] = {}
        for clause in clauses:
            for lit in clause:
                var = abs(lit)
                if var not in assignment:
                    if var not in literal_polarity:
                        literal_polarity[var] = set()
                    literal_polarity[var].add(lit > 0)

        for var, polarities in literal_polarity.items():
            if len(polarities) == 1:
                val = polarities.pop()
                assignment[var] = val
                lit = var if val else -var
                clauses = self._simplify(clauses, lit)
                if clauses is None:
                    return [], assignment

        return clauses, assignment

    def _select_variable(self, clauses: List[List[int]],
                         assignment: Dict[int, bool]) -> Optional[int]:
        """
        MOMS heuristic: En küçük clause'larda en sık görünen
        değişkeni seçer.
        """
        counts = Counter()
        min_size = float('inf')

        for clause in clauses:
            unassigned = [l for l in clause if abs(l) not in assignment]
            if unassigned:
                size = len(unassigned)
                min_size = min(min_size, size)

        for clause in clauses:
            unassigned = [l for l in clause if abs(l) not in assignment]
            if len(unassigned) <= min_size + 1:
                for lit in unassigned:
                    counts[abs(lit)] += 1

        if counts:
            return counts.most_common(1)[0][0]
        return None

    def _dpll(self, clauses: List[List[int]],
              assignment: Dict[int, bool]) -> Optional[Dict[int, bool]]:
        """Ana DPLL özyinelemeli fonksiyonu."""
        # 1. Unit Propagation
        result = self._unit_propagation(clauses, assignment.copy())
        if result[0] is None:
            return None
        clauses, assignment = result

        # 2. Pure Literal Elimination
        clauses, assignment = self._pure_literal_elimination(clauses, assignment)

        # 3. Base cases
        if len(clauses) == 0:
            return assignment  # Tüm clause'lar satisfied

        if any(len(c) == 0 for c in clauses):
            return None  # Boş clause -> conflict

        # 4. Branching
        var = self._select_variable(clauses, assignment)
        if var is None:
            return assignment

        self.stats['decisions'] += 1

        # True branch
        new_assignment = assignment.copy()
        new_assignment[var] = True
        new_clauses = self._simplify(clauses, var)
        if new_clauses is not None:
            result = self._dpll(new_clauses, new_assignment)
            if result is not None:
                return result

        # False branch (backtrack)
        self.stats['backtracks'] += 1
        new_assignment = assignment.copy()
        new_assignment[var] = False
        new_clauses = self._simplify(clauses, -var)
        if new_clauses is not None:
            result = self._dpll(new_clauses, new_assignment)
            if result is not None:
                return result

        return None

    def solve(self) -> Tuple[str, Optional[Dict[int, bool]]]:
        """
        DPLL ile SAT problemini çözer.

        Returns:
            (status, model): ('SAT', {1: True, 2: False, ...}) veya ('UNSAT', None)
        """
        start = time.perf_counter()
        initial_clauses = [c[:] for c in self.cnf.clauses]

        result = self._dpll(initial_clauses, {})

        elapsed = time.perf_counter() - start
        self.stats['time'] = elapsed

        if result is not None:
            self.stats['status'] = 'SAT'
            # Atanmamış değişkenlere default değer ver
            for v in range(1, self.cnf.num_vars + 1):
                if v not in result:
                    result[v] = True
            return 'SAT', result
        else:
            self.stats['status'] = 'UNSAT'
            return 'UNSAT', None

    def get_stats(self) -> dict:
        return self.stats.copy()
