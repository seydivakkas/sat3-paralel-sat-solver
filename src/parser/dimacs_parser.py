"""
DIMACS CNF Format Parser
========================
DIMACS formatındaki SAT problemlerini parse eder.

Format:
  c yorum satırı
  p cnf <değişken_sayısı> <clause_sayısı>
  1 -2 3 0    -> (x1 ∨ ¬x2 ∨ x3)
"""

from typing import List, Tuple, Optional
import os


class CNFFormula:
    """CNF (Conjunctive Normal Form) formülünü temsil eder."""

    def __init__(self, num_vars: int = 0, num_clauses: int = 0,
                 clauses: Optional[List[List[int]]] = None):
        self.num_vars = num_vars
        self.num_clauses = num_clauses
        self.clauses: List[List[int]] = clauses if clauses is not None else []

    def add_clause(self, clause: List[int]):
        self.clauses.append(clause)
        self.num_clauses = len(self.clauses)

    def get_variables(self) -> set:
        """Formüldeki tüm değişkenleri döndürür."""
        variables = set()
        for clause in self.clauses:
            for literal in clause:
                variables.add(abs(literal))
        return variables

    def print_formula(self):
        """Formülü okunabilir şekilde yazdırır."""
        parts = []
        for clause in self.clauses:
            literals = []
            for lit in clause:
                if lit > 0:
                    literals.append(f"x{lit}")
                else:
                    literals.append(f"¬x{abs(lit)}")
            parts.append(f"({' ∨ '.join(literals)})")
        print(" ∧ ".join(parts))

    def to_dimacs(self) -> str:
        """Formülü DIMACS formatına çevirir."""
        lines = [f"c SAT3 Problemi - Auto Generated"]
        lines.append(f"p cnf {self.num_vars} {self.num_clauses}")
        for clause in self.clauses:
            lines.append(" ".join(str(l) for l in clause) + " 0")
        return "\n".join(lines)

    def __repr__(self):
        return f"CNFFormula(vars={self.num_vars}, clauses={self.num_clauses})"


def parse_dimacs(filename: str) -> CNFFormula:
    """
    DIMACS CNF dosyasını parse eder.

    Args:
        filename: .cnf dosya yolu

    Returns:
        CNFFormula nesnesi

    Raises:
        FileNotFoundError: Dosya bulunamazsa
        ValueError: Geçersiz format
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Dosya bulunamadı: {filename}")

    formula = CNFFormula()
    declared_vars = 0
    declared_clauses = 0

    with open(filename, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Boş satır veya yorum
            if not line or line.startswith('c') or line.startswith('%'):
                continue

            # Header satırı
            if line.startswith('p cnf'):
                parts = line.split()
                if len(parts) < 4:
                    raise ValueError(
                        f"Satır {line_num}: Geçersiz header: {line}")
                declared_vars = int(parts[2])
                declared_clauses = int(parts[3])
                formula.num_vars = declared_vars
                continue

            # Clause satırı
            try:
                tokens = line.split()
                clause = []
                for token in tokens:
                    val = int(token)
                    if val == 0:
                        break
                    clause.append(val)
                if clause:
                    formula.add_clause(clause)
            except ValueError:
                raise ValueError(
                    f"Satır {line_num}: Geçersiz clause: {line}")

    # Doğrulama
    if formula.num_vars == 0:
        raise ValueError("Header satırı (p cnf ...) bulunamadı")

    # num_clauses'u gerçek clause sayısıyla güncelle
    formula.num_clauses = len(formula.clauses)

    return formula


def parse_dimacs_string(content: str) -> CNFFormula:
    """String formatındaki DIMACS içeriğini parse eder."""
    formula = CNFFormula()

    for line in content.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('c'):
            continue
        if line.startswith('p cnf'):
            parts = line.split()
            formula.num_vars = int(parts[2])
            continue
        clause = [int(x) for x in line.split() if int(x) != 0]
        if clause:
            formula.add_clause(clause)

    return formula
