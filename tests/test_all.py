"""
SAT3 Test Suite
===============
Parser, solver ve verifier için kapsamlı testler.
"""

import os
import sys
import pytest
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.parser.dimacs_parser import CNFFormula, parse_dimacs, parse_dimacs_string
from src.solvers.brute_force import BruteForceSolver
from src.solvers.parallel_brute_force import ParallelBruteForceSolver
from src.solvers.dpll import DPLLSolver
from src.solvers.resolution import ResolutionSolver
from src.utils.verifier import verify_solution, validate_cnf_file


# ============================================================
# PARSER TESTLERİ
# ============================================================

class TestParser:
    def test_basic_parse(self):
        content = "p cnf 3 2\n1 2 3 0\n-1 -2 -3 0\n"
        cnf = parse_dimacs_string(content)
        assert cnf.num_vars == 3
        assert cnf.num_clauses == 2
        assert cnf.clauses == [[1, 2, 3], [-1, -2, -3]]

    def test_comments_skipped(self):
        content = "c comment\nc another\np cnf 2 1\n1 -2 0\n"
        cnf = parse_dimacs_string(content)
        assert cnf.num_vars == 2
        assert len(cnf.clauses) == 1

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_dimacs("nonexistent.cnf")

    def test_cnf_formula_repr(self):
        cnf = CNFFormula(3, 2, [[1, 2], [-1, -2]])
        assert "vars=3" in repr(cnf)

    def test_to_dimacs(self):
        cnf = CNFFormula(3, 2, [[1, 2, 3], [-1, -2, -3]])
        text = cnf.to_dimacs()
        assert "p cnf 3 2" in text
        assert "1 2 3 0" in text

    def test_get_variables(self):
        cnf = CNFFormula(3, 1, [[1, -2, 3]])
        assert cnf.get_variables() == {1, 2, 3}


# ============================================================
# BRUTE FORCE TESTLERİ
# ============================================================

class TestBruteForce:
    def test_simple_sat(self):
        """(x1 OR x2) -> SAT"""
        cnf = CNFFormula(2, 1, [[1, 2]])
        bf = BruteForceSolver(cnf)
        status, model = bf.solve()
        assert status == 'SAT'
        assert model is not None

    def test_simple_unsat(self):
        """(x1) AND (NOT x1) -> UNSAT"""
        cnf = CNFFormula(1, 2, [[1], [-1]])
        bf = BruteForceSolver(cnf)
        status, model = bf.solve()
        assert status == 'UNSAT'
        assert model is None

    def test_3sat_satisfiable(self):
        """(x1 OR x2 OR x3) AND (NOT x1 OR x2 OR x3)"""
        cnf = CNFFormula(3, 2, [[1, 2, 3], [-1, 2, 3]])
        bf = BruteForceSolver(cnf)
        status, model = bf.solve()
        assert status == 'SAT'
        # Çözümü doğrula
        valid, _ = verify_solution(cnf, model)
        assert valid

    def test_solution_verification(self):
        cnf = CNFFormula(3, 3, [[1, 2, 3], [-1, 2, -3], [1, -2, 3]])
        bf = BruteForceSolver(cnf)
        status, model = bf.solve()
        if status == 'SAT':
            valid, failed = verify_solution(cnf, model)
            assert valid
            assert len(failed) == 0

    def test_stats(self):
        cnf = CNFFormula(2, 1, [[1, 2]])
        bf = BruteForceSolver(cnf)
        bf.solve()
        stats = bf.get_stats()
        assert stats['time'] > 0
        assert stats['status'] in ('SAT', 'UNSAT')


# ============================================================
# PARALLEL BRUTE FORCE TESTLERİ
# ============================================================

class TestParallelBruteForce:
    def test_simple_sat(self):
        cnf = CNFFormula(3, 2, [[1, 2, 3], [-1, 2, -3]])
        pbf = ParallelBruteForceSolver(cnf, num_processes=2)
        status, model = pbf.solve()
        assert status == 'SAT'
        if model:
            valid, _ = verify_solution(cnf, model)
            assert valid

    def test_simple_unsat(self):
        cnf = CNFFormula(1, 2, [[1], [-1]])
        pbf = ParallelBruteForceSolver(cnf, num_processes=2)
        status, model = pbf.solve()
        assert status == 'UNSAT'

    def test_agrees_with_serial(self):
        """Paralel ve seri aynı sonucu vermeli."""
        cnf = CNFFormula(5, 5, [
            [1, 2, 3], [-1, -2, 4], [3, 4, 5],
            [-2, -3, -5], [1, -4, 5]
        ])
        bf = BruteForceSolver(cnf)
        pbf = ParallelBruteForceSolver(cnf, num_processes=2)

        status_s, _ = bf.solve()
        status_p, _ = pbf.solve()
        assert status_s == status_p


# ============================================================
# DPLL TESTLERİ
# ============================================================

class TestDPLL:
    def test_simple_sat(self):
        cnf = CNFFormula(2, 1, [[1, 2]])
        dpll = DPLLSolver(cnf)
        status, model = dpll.solve()
        assert status == 'SAT'
        assert model is not None

    def test_simple_unsat(self):
        cnf = CNFFormula(1, 2, [[1], [-1]])
        dpll = DPLLSolver(cnf)
        status, model = dpll.solve()
        assert status == 'UNSAT'

    def test_unit_propagation(self):
        """(x1) AND (x1 OR x2) -> x1=True"""
        cnf = CNFFormula(2, 2, [[1], [1, 2]])
        dpll = DPLLSolver(cnf)
        status, model = dpll.solve()
        assert status == 'SAT'
        assert model[1] == True

    def test_complex_sat(self):
        cnf = CNFFormula(4, 4, [
            [1, 2, 3], [-1, 2, 4], [1, -3, 4], [-2, 3, -4]
        ])
        dpll = DPLLSolver(cnf)
        status, model = dpll.solve()
        assert status == 'SAT'
        valid, _ = verify_solution(cnf, model)
        assert valid

    def test_agrees_with_brute_force(self):
        """DPLL ve BF aynı SAT/UNSAT sonucu vermeli."""
        cnf = CNFFormula(5, 6, [
            [1, 2, 3], [-1, -2, 4], [3, 4, 5],
            [-2, -3, -5], [1, -4, 5], [-1, 2, -3]
        ])
        bf = BruteForceSolver(cnf)
        dpll = DPLLSolver(cnf)
        status_bf, _ = bf.solve()
        status_dpll, _ = dpll.solve()
        assert status_bf == status_dpll

    def test_stats(self):
        cnf = CNFFormula(3, 3, [[1, 2, 3], [-1, 2, -3], [1, -2, 3]])
        dpll = DPLLSolver(cnf)
        dpll.solve()
        stats = dpll.get_stats()
        assert 'decisions' in stats
        assert 'unit_propagations' in stats


# ============================================================
# RESOLUTION TESTLERİ
# ============================================================

class TestResolution:
    def test_simple_unsat(self):
        """(x1) AND (NOT x1) -> UNSAT"""
        cnf = CNFFormula(1, 2, [[1], [-1]])
        res = ResolutionSolver(cnf)
        status, _ = res.solve()
        assert status == 'UNSAT'

    def test_simple_sat(self):
        """(x1 OR x2) -> SAT (resolution yeni clause üretemez)"""
        cnf = CNFFormula(2, 1, [[1, 2]])
        res = ResolutionSolver(cnf)
        status, _ = res.solve()
        assert status == 'SAT'

    def test_resolution_stats(self):
        cnf = CNFFormula(2, 3, [[1, 2], [-1, 2], [1, -2]])
        res = ResolutionSolver(cnf)
        res.solve()
        stats = res.get_stats()
        assert 'resolutions' in stats


# ============================================================
# VERIFIER TESTLERİ
# ============================================================

class TestVerifier:
    def test_valid_solution(self):
        cnf = CNFFormula(2, 2, [[1, 2], [-1, 2]])
        model = {1: False, 2: True}
        valid, failed = verify_solution(cnf, model)
        assert valid
        assert len(failed) == 0

    def test_invalid_solution(self):
        cnf = CNFFormula(2, 2, [[1], [-1]])
        model = {1: True}
        valid, failed = verify_solution(cnf, model)
        assert not valid

    def test_validate_cnf_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cnf',
                                         delete=False) as f:
            f.write("p cnf 2 1\n1 -2 0\n")
            f.flush()
            valid, errors = validate_cnf_file(f.name)
        os.unlink(f.name)
        assert valid

    def test_validate_nonexistent(self):
        valid, errors = validate_cnf_file("no_such_file.cnf")
        assert not valid


# ============================================================
# CROSS-VALIDATION TESTLERİ
# ============================================================

class TestCrossValidation:
    """Farklı solver'ların aynı sonucu vermesini doğrular."""

    @pytest.fixture
    def sat_problem(self):
        return CNFFormula(4, 3, [[1, 2, 3], [-1, 2, 4], [1, -3, 4]])

    @pytest.fixture
    def unsat_problem(self):
        return CNFFormula(2, 4, [[1], [-1], [2], [-2]])

    def test_all_solvers_agree_sat(self, sat_problem):
        bf_status, _ = BruteForceSolver(sat_problem).solve()
        dpll_status, _ = DPLLSolver(sat_problem).solve()
        assert bf_status == dpll_status == 'SAT'

    def test_all_solvers_agree_unsat(self, unsat_problem):
        bf_status, _ = BruteForceSolver(unsat_problem).solve()
        dpll_status, _ = DPLLSolver(unsat_problem).solve()
        res_status, _ = ResolutionSolver(unsat_problem).solve()
        assert bf_status == 'UNSAT'
        assert dpll_status == 'UNSAT'
        assert res_status == 'UNSAT'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
