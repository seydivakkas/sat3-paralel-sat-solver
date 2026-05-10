"""
DIMACS CNF Problem Generator
=============================
10 adet farklı zorlukta 3-SAT problemi oluşturur.
En az 1 tanesi UNSAT olacak şekilde tasarlanmıştır.
"""

import random
import os

def generate_random_3sat(num_vars: int, num_clauses: int,
                         seed: int = None) -> str:
    """Rastgele 3-SAT problemi oluşturur."""
    if seed is not None:
        random.seed(seed)

    lines = [f"c SAT3 Problemi - Random 3-SAT"]
    lines.append(f"c Degisken: {num_vars}, Clause: {num_clauses}")
    lines.append(f"p cnf {num_vars} {num_clauses}")

    for _ in range(num_clauses):
        # 3 farklı değişken seç
        vars_selected = random.sample(range(1, num_vars + 1), min(3, num_vars))
        clause = []
        for v in vars_selected:
            if random.random() < 0.5:
                clause.append(v)
            else:
                clause.append(-v)
        lines.append(" ".join(str(l) for l in clause) + " 0")

    return "\n".join(lines)


def generate_unsat_problem(num_vars: int) -> str:
    """Kesinlikle UNSAT olan bir problem oluşturur.
    (x1) AND (¬x1) gibi çelişki içerir.
    """
    lines = [f"c SAT3 Problemi - UNSAT Problem"]
    # Her değişken için hem pozitif hem negatif unit clause ekle
    clauses = []
    for v in range(1, num_vars + 1):
        clauses.append(f"{v} 0")
        clauses.append(f"-{v} 0")
    # Ek clause'lar ekle
    num_extra = num_vars * 2
    for _ in range(num_extra):
        vars_selected = random.sample(range(1, num_vars + 1), min(3, num_vars))
        clause = []
        for v in vars_selected:
            clause.append(v if random.random() < 0.5 else -v)
        clauses.append(" ".join(str(l) for l in clause) + " 0")

    total = len(clauses)
    lines.append(f"c Degisken: {num_vars}, Clause: {total}")
    lines.append(f"p cnf {num_vars} {total}")
    lines.extend(clauses)
    return "\n".join(lines)


def generate_all_problems(output_dir: str = "test_cnf"):
    """10 adet test problemi oluşturur."""
    os.makedirs(output_dir, exist_ok=True)

    problems = [
        # (num_vars, num_clauses, seed, is_unsat)
        (5,   10,  42,   False),   # problem01: Çok kolay
        (8,   20,  123,  False),   # problem02: Kolay
        (10,  30,  456,  False),   # problem03: Orta-kolay
        (12,  40,  789,  False),   # problem04: Orta
        (15,  50,  1001, False),   # problem05: Orta-zor
        (5,   0,   None, True),    # problem06: UNSAT (5 değişken)
        (18,  70,  2002, False),   # problem07: Zor
        (20,  85,  3003, False),   # problem08: Çok zor
        (10,  0,   None, True),    # problem09: UNSAT (10 değişken)
        (22,  91,  4004, False),   # problem10: En zor
    ]

    for i, (n_vars, n_clauses, seed, is_unsat) in enumerate(problems, 1):
        filename = os.path.join(output_dir, f"problem{i:02d}.cnf")
        if is_unsat:
            content = generate_unsat_problem(n_vars)
        else:
            content = generate_random_3sat(n_vars, n_clauses, seed)

        with open(filename, 'w') as f:
            f.write(content)
        print(f"[OK] {filename} oluşturuldu ({n_vars} değişken)")

    print(f"\nToplam {len(problems)} problem oluşturuldu.")


if __name__ == "__main__":
    generate_all_problems()
