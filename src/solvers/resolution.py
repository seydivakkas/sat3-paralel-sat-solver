"""
Resolution SAT Solver
=====================
Resolution (çözünürlük) algoritması ile SAT çözücüsü.
Kural: (A ∨ x) ve (B ∨ ¬x) → (A ∨ B)
Empty clause oluşursa UNSAT, yeni clause üretilemezse SAT.
"""

import time
from typing import Optional, Tuple, FrozenSet, Set, Dict
from itertools import combinations


class ResolutionSolver:
    """Resolution algoritması tabanlı SAT çözücüsü."""

    def __init__(self, cnf):
        self.cnf = cnf
        # Clause'ları frozenset olarak sakla (hashable, tekrarı önler)
        self.clause_set: Set[FrozenSet[int]] = set()
        for clause in cnf.clauses:
            self.clause_set.add(frozenset(clause))
        self.stats = {
            'resolutions': 0,
            'new_clauses': 0,
            'time': 0.0,
            'status': None
        }

    def _is_tautology(self, clause: FrozenSet[int]) -> bool:
        """Clause tautology mi? (x ve ¬x aynı clause'da)"""
        for lit in clause:
            if -lit in clause:
                return True
        return False

    def _resolve(self, c1: FrozenSet[int],
                 c2: FrozenSet[int]) -> Optional[FrozenSet[int]]:
        """
        İki clause arasında resolution uygula.
        Tam olarak bir complementary literal çifti olmalı.

        Returns:
            Resolvent clause veya None
        """
        complementary = []
        for lit in c1:
            if -lit in c2:
                complementary.append(lit)

        # Tam olarak 1 complementary literal olmalı
        if len(complementary) != 1:
            return None

        pivot = complementary[0]
        # Resolvent: c1'den pivot'u, c2'den -pivot'u çıkar, birleştir
        resolvent = (c1 - {pivot}) | (c2 - {-pivot})

        # Tautology kontrolü
        if self._is_tautology(resolvent):
            return None

        return resolvent

    def _subsumes(self, c1: FrozenSet[int],
                  c2: FrozenSet[int]) -> bool:
        """c1, c2'yi subsume eder mi? (c1 ⊆ c2)"""
        return c1.issubset(c2)

    def solve(self, max_clause_size: int = 10,
              max_iterations: int = 10000,
              timeout: float = 10.0) -> Tuple[str, Optional[Dict[int, bool]]]:
        """
        Resolution algoritması ile SAT/UNSAT belirler.

        Args:
            max_clause_size: Saklanacak maksimum clause boyutu
            max_iterations: Maksimum iterasyon sayısı
            timeout: Maksimum calisma suresi (saniye)

        Returns:
            (status, model): ('SAT', None) veya ('UNSAT', None)
            Not: Resolution SAT durumunda model uretmez.
        """
        start = time.perf_counter()
        clauses = set(self.clause_set)
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            new_resolvents: Set[FrozenSet[int]] = set()

            # Timeout kontrolu
            if time.perf_counter() - start > timeout:
                break

            clause_list = list(clauses)
            for i in range(len(clause_list)):
                # Timeout kontrolu (ic dongude)
                if time.perf_counter() - start > timeout:
                    break
                for j in range(i + 1, len(clause_list)):
                    c1 = clause_list[i]
                    c2 = clause_list[j]

                    resolvent = self._resolve(c1, c2)
                    if resolvent is None:
                        continue

                    self.stats['resolutions'] += 1

                    # Empty clause -> UNSAT
                    if len(resolvent) == 0:
                        elapsed = time.perf_counter() - start
                        self.stats['time'] = elapsed
                        self.stats['status'] = 'UNSAT'
                        return 'UNSAT', None

                    # Boyut sınırı
                    if len(resolvent) > max_clause_size:
                        continue

                    # Yeni clause mı?
                    if resolvent not in clauses:
                        # Subsumption kontrolü
                        subsumed = False
                        for existing in clauses:
                            if self._subsumes(existing, resolvent):
                                subsumed = True
                                break
                        if not subsumed:
                            new_resolvents.add(resolvent)

            if not new_resolvents:
                # Yeni clause üretilmedi -> SAT
                elapsed = time.perf_counter() - start
                self.stats['time'] = elapsed
                self.stats['status'] = 'SAT'
                self.stats['new_clauses'] = len(clauses) - len(self.clause_set)
                return 'SAT', None

            self.stats['new_clauses'] += len(new_resolvents)
            clauses.update(new_resolvents)

            # Bellek sınırı kontrolü
            if len(clauses) > 50000:
                break

        elapsed = time.perf_counter() - start
        self.stats['time'] = elapsed
        self.stats['status'] = 'UNKNOWN'
        return 'UNKNOWN', None

    def get_stats(self) -> dict:
        return self.stats.copy()
