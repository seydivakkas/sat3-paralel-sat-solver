"""
Solution Verifier
=================
SAT çözümlerini doğrular ve DIMACS dosyalarını validate eder.
"""

import os
from typing import Dict, List, Tuple


def verify_solution(cnf, model: Dict[int, bool]) -> Tuple[bool, List[int]]:
    """
    Bulunan çözümün gerçekten formülü sağlayıp sağlamadığını doğrular.

    Args:
        cnf: CNFFormula nesnesi
        model: {1: True, 2: False, ...} formatta çözüm

    Returns:
        (is_valid, failed_clauses): Doğruluk ve başarısız clause indeksleri
    """
    failed_clauses = []

    for idx, clause in enumerate(cnf.clauses):
        clause_satisfied = False
        for literal in clause:
            var = abs(literal)
            if var not in model:
                continue  # Atanmamış değişken (default True kabul)
            val = model[var]
            if (literal > 0 and val) or (literal < 0 and not val):
                clause_satisfied = True
                break

        if not clause_satisfied:
            failed_clauses.append(idx)

    return len(failed_clauses) == 0, failed_clauses


def validate_cnf_file(filename: str) -> Tuple[bool, List[str]]:
    """
    DIMACS CNF dosyasının formatını doğrular.

    Args:
        filename: .cnf dosya yolu

    Returns:
        (is_valid, errors): Doğruluk ve hata mesajları listesi
    """
    errors = []

    if not os.path.exists(filename):
        return False, [f"Dosya bulunamadı: {filename}"]

    has_header = False
    declared_vars = 0
    declared_clauses = 0
    actual_clauses = 0
    max_var_seen = 0

    with open(filename, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            if not line or line.startswith('c') or line.startswith('%'):
                continue

            if line.startswith('p cnf'):
                if has_header:
                    errors.append(f"Satır {line_num}: Birden fazla header")
                has_header = True
                parts = line.split()
                if len(parts) < 4:
                    errors.append(f"Satır {line_num}: Eksik header bilgisi")
                    continue
                try:
                    declared_vars = int(parts[2])
                    declared_clauses = int(parts[3])
                except ValueError:
                    errors.append(f"Satır {line_num}: Header'da geçersiz sayı")
                continue

            # Clause satırı
            try:
                tokens = line.split()
                has_zero = False
                for token in tokens:
                    val = int(token)
                    if val == 0:
                        has_zero = True
                        break
                    max_var_seen = max(max_var_seen, abs(val))

                if has_zero:
                    actual_clauses += 1
                else:
                    errors.append(
                        f"Satır {line_num}: Clause 0 ile bitmiyor")
            except ValueError:
                errors.append(f"Satır {line_num}: Geçersiz literal")

    if not has_header:
        errors.append("Header satırı (p cnf ...) bulunamadı")

    if max_var_seen > declared_vars:
        errors.append(
            f"Değişken {max_var_seen} kullanılmış ama header {declared_vars} bildiriyor")

    return len(errors) == 0, errors
