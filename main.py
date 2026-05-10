"""
SAT3 Paralel Programlama Projesi - Ana Calistirici
====================================================
10 DIMACS problemi uzerinde 4 farkli solver calistirir.
"""

import os
import sys
import time
import glob

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.parser.dimacs_parser import parse_dimacs
from src.solvers.brute_force import BruteForceSolver
from src.solvers.parallel_brute_force import ParallelBruteForceSolver
from src.solvers.dpll import DPLLSolver
from src.solvers.resolution import ResolutionSolver
from src.utils.verifier import verify_solution
from src.utils.formatter import (
    export_to_csv, export_to_json, generate_summary_table
)
from src.analysis.performance import PerformanceAnalyzer


def log(msg):
    print(msg, flush=True)


def solve_all_problems():
    cnf_dir = os.path.join(PROJECT_ROOT, 'test_cnf')
    cnf_files = sorted(glob.glob(os.path.join(cnf_dir, '*.cnf')))

    if not cnf_files:
        log("[HATA] test_cnf/ klasorunde .cnf dosyasi bulunamadi!")
        return

    log("=" * 70)
    log("  SAT3 PARALEL PROGRAMLAMA PROJESI")
    log("  Seydi Vakkas Eryilmaz")
    log("=" * 70)

    results = []
    analyzer = PerformanceAnalyzer()
    thread_counts = [2, 4]

    for cnf_file in cnf_files:
        problem_name = os.path.basename(cnf_file)
        log(f"\n{'-' * 60}")
        log(f"  [PROBLEM] {problem_name}")
        log(f"{'-' * 60}")

        cnf = parse_dimacs(cnf_file)
        log(f"  Degisken: {cnf.num_vars}, Clause: {cnf.num_clauses}")

        # ---- 1. DPLL (en hizli) ----
        log(f"  [1] DPLL Solver...")
        dpll = DPLLSolver(cnf)
        status_d, model_d = dpll.solve()
        stats_d = dpll.get_stats()

        result_d = {
            'problem': problem_name, 'solver': 'DPLL',
            'status': status_d, 'time': stats_d['time'],
            'model': model_d, 'stats': stats_d,
            'num_vars': cnf.num_vars, 'num_clauses': cnf.num_clauses
        }
        results.append(result_d)
        analyzer.add_result(problem_name, 'DPLL', stats_d['time'],
                            num_threads=1, status=status_d,
                            num_vars=cnf.num_vars, num_clauses=cnf.num_clauses)

        if model_d:
            valid, _ = verify_solution(cnf, model_d)
            v_str = "[OK]" if valid else "[FAIL]"
            log(f"       Durum: {status_d} | Sure: {stats_d['time']:.6f}s | "
                f"Karar: {stats_d['decisions']} | Dogrulama: {v_str}")
        else:
            log(f"       Durum: {status_d} | Sure: {stats_d['time']:.6f}s | "
                f"Karar: {stats_d['decisions']}")

        is_sat = (status_d == 'SAT')

        # ---- 2. RESOLUTION (timeout=5s) ----
        log(f"  [2] Resolution Solver...")
        res = ResolutionSolver(cnf)
        status_r, model_r = res.solve(max_clause_size=6,
                                       max_iterations=500,
                                       timeout=5.0)
        stats_r = res.get_stats()

        result_r = {
            'problem': problem_name, 'solver': 'Resolution',
            'status': status_r, 'time': stats_r['time'],
            'model': model_r, 'stats': stats_r,
            'num_vars': cnf.num_vars, 'num_clauses': cnf.num_clauses
        }
        results.append(result_r)
        analyzer.add_result(problem_name, 'Resolution', stats_r['time'],
                            num_threads=1, status=status_r,
                            num_vars=cnf.num_vars, num_clauses=cnf.num_clauses)

        log(f"       Durum: {status_r} | Sure: {stats_r['time']:.6f}s | "
            f"Cozunurlukler: {stats_r['resolutions']}")

        # ---- 3. BRUTE FORCE (seri, sadece n<=15) ----
        bf_limit = 15
        if cnf.num_vars <= bf_limit:
            bf_timeout = 30

            log(f"  [3] Brute Force (Seri)...")
            bf = BruteForceSolver(cnf)
            status_bf, model_bf = bf.solve(timeout=bf_timeout)
            stats_bf = bf.get_stats()

            result_bf = {
                'problem': problem_name, 'solver': 'BruteForce',
                'status': status_bf, 'time': stats_bf['time'],
                'model': model_bf, 'stats': stats_bf,
                'num_vars': cnf.num_vars, 'num_clauses': cnf.num_clauses
            }
            results.append(result_bf)
            analyzer.add_result(problem_name, 'BruteForce', stats_bf['time'],
                                num_threads=1, status=status_bf,
                                num_vars=cnf.num_vars, num_clauses=cnf.num_clauses)

            if model_bf:
                valid, _ = verify_solution(cnf, model_bf)
                v_str = "[OK]" if valid else "[FAIL]"
                log(f"       Durum: {status_bf} | Sure: {stats_bf['time']:.6f}s | "
                    f"Dogrulama: {v_str}")
            else:
                log(f"       Durum: {status_bf} | Sure: {stats_bf['time']:.6f}s")

            serial_time = stats_bf['time']

            # ---- 4. PARALLEL BRUTE FORCE ----
            if is_sat:
                for num_threads in thread_counts:
                    log(f"  [4] Parallel BF ({num_threads} thread)...")
                    pbf = ParallelBruteForceSolver(cnf, num_processes=num_threads)
                    status_p, model_p = pbf.solve(timeout=bf_timeout)
                    stats_p = pbf.get_stats()

                    result_p = {
                        'problem': problem_name,
                        'solver': f'ParallelBF-{num_threads}T',
                        'status': status_p, 'time': stats_p['time'],
                        'model': model_p, 'stats': stats_p,
                        'num_vars': cnf.num_vars, 'num_clauses': cnf.num_clauses
                    }
                    results.append(result_p)
                    analyzer.add_result(
                        problem_name, 'ParallelBF',
                        stats_p['time'], num_threads=num_threads,
                        status=status_p, num_vars=cnf.num_vars,
                        num_clauses=cnf.num_clauses
                    )

                    if serial_time > 0 and stats_p['time'] > 0:
                        speedup = serial_time / stats_p['time']
                        efficiency = speedup / num_threads
                        log(f"       Durum: {status_p} | Sure: {stats_p['time']:.6f}s | "
                            f"Speedup: {speedup:.2f}x | Eff: {efficiency:.2%}")
                    else:
                        log(f"       Durum: {status_p} | Sure: {stats_p['time']:.6f}s")
        else:
            log(f"  [3] Brute Force --> ATLANDI (n={cnf.num_vars} > {bf_limit})")

    # ---- SONUCLARI KAYDET ----
    log(f"\n{'=' * 70}")
    log("  SONUCLAR")
    log(f"{'=' * 70}\n")

    table = generate_summary_table(results)
    log(table)

    results_dir = os.path.join(PROJECT_ROOT, 'results')
    os.makedirs(results_dir, exist_ok=True)

    export_to_csv(results, os.path.join(results_dir, 'results.csv'))
    export_to_json(results, os.path.join(results_dir, 'results.json'))
    log(f"\n[OK] Sonuclar kaydedildi: results/results.csv, results/results.json")

    plots_dir = os.path.join(PROJECT_ROOT, 'plots')
    analyzer.generate_all_plots(plots_dir)
    analyzer.save_metrics(os.path.join(results_dir, 'metrics.json'))

    speedup_data = analyzer.get_speedup_data()
    if speedup_data:
        log(f"\n{'=' * 70}")
        log("  SPEEDUP OZETI")
        log(f"{'=' * 70}")
        log(f"{'Problem':<18} {'Threads':<10} {'Seri (s)':<12} "
            f"{'Paralel (s)':<12} {'Speedup':<10} {'Efficiency':<10}")
        log("-" * 72)
        for problem, tdata in speedup_data.items():
            for threads, d in sorted(tdata.items()):
                log(f"{problem:<18} {threads:<10} "
                    f"{d['serial_time']:<12.6f} "
                    f"{d['parallel_time']:<12.6f} "
                    f"{d['speedup']:<10.4f} "
                    f"{d['efficiency']:<10.4f}")

    log(f"\n{'=' * 70}")
    log("  TUM ISLEMLER TAMAMLANDI")
    log(f"{'=' * 70}")


if __name__ == '__main__':
    solve_all_problems()
