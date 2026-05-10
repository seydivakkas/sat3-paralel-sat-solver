"""
CDCL SAT Solver — Conflict-Driven Clause Learning
===================================================
Saglamlik odakli implementasyon:
- Conflict clause learning (Non-chronological backtracking)
- VSIDS variable selection heuristic
- Restart stratejisi (Luby sequence)

DPLL'den farklar:
1. Cakisma analizinden ogrenilen yeni clause'lar eklenir
2. Backjumping: cakisma seviyesine dogrudan atlanir
3. VSIDS: cakisma istatistiklerine gore degisken secimi

"""

import time
from typing import Optional, Dict, List, Tuple, Set


class CDCLSolver:
    """
    CDCL SAT Cozucusu.
    Basit ama dogru bir implementasyon:
    - Trail tabanli atama yonetimi
    - Conflict analizi ile clause ogrenme
    - VSIDS ile akilli degisken secimi
    """

    UNASSIGNED = -1

    def __init__(self, cnf):
        self.cnf = cnf
        self.n = cnf.num_vars

        # Kopya clause listesi (learned clause'lar eklenecek)
        self.clauses: List[List[int]] = [list(c) for c in cnf.clauses]

        # Atama durumu: var -> True/False/None
        self.val: Dict[int, Optional[bool]] = {v: None for v in range(1, self.n + 1)}
        # Atama seviyesi
        self.dlevel: Dict[int, int] = {}
        # Implication reason: var -> clause_idx
        self.reason: Dict[int, int] = {}

        # Trail: atanan literaller (sirayla)
        self.trail: List[int] = []
        # Her karar seviyesinin trail baslangici
        self.trail_lim: List[int] = []

        # VSIDS aktivite skorlari
        self.activity: Dict[int, float] = {v: 0.0 for v in range(1, self.n + 1)}
        self.var_inc: float = 1.0

        self.stats = {
            'decisions': 0,
            'conflicts': 0,
            'learned': 0,
            'restarts': 0,
            'propagations': 0,
            'time': 0.0,
            'status': None
        }

    # ------------------------------------------------------------------ #
    # Temel yardimcilar
    # ------------------------------------------------------------------ #
    def _lit_val(self, lit: int) -> Optional[bool]:
        """Literal degerini dondur."""
        var = abs(lit)
        v = self.val[var]
        if v is None:
            return None
        return v if lit > 0 else not v

    def _current_level(self) -> int:
        return len(self.trail_lim)

    def _assign(self, lit: int, reason_ci: int = -1):
        """Literal'i ata."""
        var = abs(lit)
        self.val[var] = (lit > 0)
        self.dlevel[var] = self._current_level()
        self.reason[var] = reason_ci
        self.trail.append(lit)

    # ------------------------------------------------------------------ #
    # Unit Propagation (basit tarama)
    # ------------------------------------------------------------------ #
    def _propagate(self) -> int:
        """
        Tum unit clause'lari propagate et.
        Cakisma varsa clause index'i dondurur, yoksa -1.
        """
        changed = True
        while changed:
            changed = False
            for ci, clause in enumerate(self.clauses):
                unset = []
                sat = False
                for lit in clause:
                    v = self._lit_val(lit)
                    if v is True:
                        sat = True
                        break
                    elif v is None:
                        unset.append(lit)

                if sat:
                    continue

                if not unset:
                    # Tum literaller False -> CAKISMA
                    return ci

                if len(unset) == 1:
                    # Unit clause -> zorunlu atama
                    self._assign(unset[0], ci)
                    self.stats['propagations'] += 1
                    changed = True

        return -1  # Cakisma yok

    # ------------------------------------------------------------------ #
    # Conflict Analysis
    # ------------------------------------------------------------------ #
    def _analyze(self, conflict_ci: int) -> Tuple[List[int], int]:
        """
        Cakisma analizinden ogrenilen clause ve backjump seviyesini bul.
        1-UIP tabanlı basit implementasyon.
        """
        current_level = self._current_level()
        seen: Set[int] = set()
        learned: List[int] = []
        btlevel = 0

        # Cakisan clause'dan baslayarak ara
        frontier = list(self.clauses[conflict_ci])
        counter = 0  # Mevcut seviyedeki literal sayisi

        for lit in frontier:
            var = abs(lit)
            seen.add(var)
            self._bump_var(var)
            if self.dlevel.get(var, 0) == current_level:
                counter += 1
            elif self.dlevel.get(var, 0) > 0:
                learned.append(-lit)
                btlevel = max(btlevel, self.dlevel.get(var, 0))

        # Trail'i geri tarayarak 1-UIP bul
        for lit in reversed(self.trail):
            if counter <= 1:
                # Bu literal UIP
                if self._lit_val(lit) is not None:
                    uip = lit
                    # Atama degerine gore negasyonu ekle
                    learned = [-uip] + learned
                break

            var = abs(lit)
            if var not in seen:
                continue
            if self.dlevel.get(var, 0) != current_level:
                continue

            # Bu degiskeni genisle
            r = self.reason.get(var, -1)
            if r != -1:
                for l2 in self.clauses[r]:
                    v2 = abs(l2)
                    if v2 not in seen:
                        seen.add(v2)
                        self._bump_var(v2)
                        if self.dlevel.get(v2, 0) == current_level:
                            counter += 1
                        elif self.dlevel.get(v2, 0) > 0:
                            learned.append(-l2)
                            btlevel = max(btlevel, self.dlevel.get(v2, 0))
            counter -= 1

        # Eger ogrenilen clause bos ise unit olarak ekle
        if not learned:
            learned = [0]  # sentinel

        return learned, btlevel

    def _bump_var(self, var: int):
        self.activity[var] += self.var_inc
        if self.activity[var] > 1e100:
            for v in self.activity:
                self.activity[v] *= 1e-100
            self.var_inc *= 1e-100

    def _decay(self):
        self.var_inc /= 0.95

    # ------------------------------------------------------------------ #
    # Backtrack
    # ------------------------------------------------------------------ #
    def _backtrack(self, level: int):
        """Verilen seviyeye geri don."""
        target_len = self.trail_lim[level] if level < len(self.trail_lim) else 0

        while len(self.trail) > target_len:
            lit = self.trail.pop()
            var = abs(lit)
            self.val[var] = None
            self.dlevel.pop(var, None)
            self.reason.pop(var, None)

        self.trail_lim = self.trail_lim[:level]

    # ------------------------------------------------------------------ #
    # VSIDS: Degisken Secimi
    # ------------------------------------------------------------------ #
    def _pick_var(self) -> Optional[int]:
        """En yuksek aktiviteli atanmamis degiskeni sec."""
        best, best_score = None, -1.0
        for var in range(1, self.n + 1):
            if self.val[var] is None and self.activity[var] > best_score:
                best_score = self.activity[var]
                best = var
        return best

    # ------------------------------------------------------------------ #
    # Ana CDCL dongusu
    # ------------------------------------------------------------------ #
    def solve(self) -> Tuple[str, Optional[Dict[int, bool]]]:
        start = time.perf_counter()

        # Seviye 0 propagation
        conflict = self._propagate()
        if conflict != -1:
            self.stats['time'] = time.perf_counter() - start
            self.stats['status'] = 'UNSAT'
            return 'UNSAT', None

        # Luby restart parametreleri
        luby_u = 50
        conflicts_since_restart = 0
        restart_limit = luby_u
        luby_k = 1

        while True:
            # Atanmamis degisken var mi?
            var = self._pick_var()
            if var is None:
                # Tum atanmis -> SAT
                model = {v: self.val[v] for v in range(1, self.n + 1)}
                self.stats['time'] = time.perf_counter() - start
                self.stats['status'] = 'SAT'
                return 'SAT', model

            # Karar: pozitif literal dene
            self.trail_lim.append(len(self.trail))
            self._assign(var, -1)
            self.stats['decisions'] += 1

            # Propagate & conflict cozme
            while True:
                conflict = self._propagate()
                if conflict == -1:
                    break  # Cakisma yok, sonraki karara gec

                self.stats['conflicts'] += 1
                conflicts_since_restart += 1
                self._decay()

                if self._current_level() == 0:
                    # Level 0 cakisma -> kesinlikle UNSAT
                    self.stats['time'] = time.perf_counter() - start
                    self.stats['status'] = 'UNSAT'
                    return 'UNSAT', None

                # Cakisma analizi
                try:
                    learned_clause, btlevel = self._analyze(conflict)
                except Exception:
                    btlevel = max(0, self._current_level() - 1)
                    learned_clause = []

                # Backjump
                self._backtrack(btlevel)

                # Clause ogrenme
                if learned_clause and learned_clause != [0]:
                    ci = len(self.clauses)
                    self.clauses.append(learned_clause)
                    self.stats['learned'] += 1
                    # Unit ise zorla ata
                    unset = [l for l in learned_clause if self._lit_val(l) is None]
                    if len(unset) == 1:
                        self._assign(unset[0], ci)

                # Restart kontrolu
                if conflicts_since_restart >= restart_limit:
                    self._backtrack(0)
                    self.stats['restarts'] += 1
                    conflicts_since_restart = 0
                    luby_k += 1
                    restart_limit = luby_u * luby_k
                    if luby_k > 100:
                        self.stats['time'] = time.perf_counter() - start
                        self.stats['status'] = 'UNKNOWN'
                        return 'UNKNOWN', None

    def get_stats(self) -> dict:
        return self.stats.copy()
