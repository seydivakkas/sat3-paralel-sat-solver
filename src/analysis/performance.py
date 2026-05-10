"""
Performance Analyzer
====================
Speedup, Efficiency hesaplama ve matplotlib ile grafik üretimi.
"""

import os
import json
from typing import List, Dict
from collections import defaultdict

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class PerformanceAnalyzer:
    """Performans metriklerini hesaplar ve grafikler üretir."""

    def __init__(self):
        self.results: List[Dict] = []

    def add_result(self, problem: str, solver: str,
                   time_sec: float, num_threads: int = 1,
                   status: str = 'SAT', num_vars: int = 0,
                   num_clauses: int = 0, **kwargs):
        self.results.append({
            'problem': problem,
            'solver': solver,
            'time': time_sec,
            'num_threads': num_threads,
            'status': status,
            'num_vars': num_vars,
            'num_clauses': num_clauses,
            **kwargs
        })

    def calculate_speedup(self, serial_time: float,
                          parallel_time: float) -> float:
        """Speedup = T_serial / T_parallel"""
        if parallel_time == 0:
            return float('inf')
        return serial_time / parallel_time

    def calculate_efficiency(self, speedup: float,
                             num_processors: int) -> float:
        """Efficiency = Speedup / P"""
        if num_processors == 0:
            return 0
        return speedup / num_processors

    def get_speedup_data(self) -> Dict[str, List]:
        """Problem bazında speedup verilerini hesaplar."""
        # Seri süreleri bul (BruteForce = seri)
        serial_times = {}
        for r in self.results:
            if r['solver'] == 'BruteForce':
                serial_times[r['problem']] = r['time']

        # Thread bazında paralel süreleri bul
        parallel_data = defaultdict(lambda: defaultdict(float))
        for r in self.results:
            if r['solver'].startswith('ParallelBF'):
                threads = r['num_threads']
                parallel_data[r['problem']][threads] = r['time']

        # Speedup hesapla
        speedup_results = {}
        for problem, par_times in parallel_data.items():
            if problem in serial_times:
                serial_t = serial_times[problem]
                speedup_results[problem] = {}
                for threads, par_t in sorted(par_times.items()):
                    sp = self.calculate_speedup(serial_t, par_t)
                    eff = self.calculate_efficiency(sp, threads)
                    speedup_results[problem][threads] = {
                        'speedup': sp,
                        'efficiency': eff,
                        'serial_time': serial_t,
                        'parallel_time': par_t
                    }
        return speedup_results

    def plot_speedup(self, output_dir: str = 'plots'):
        """Thread sayısı vs Speedup grafiği"""
        if not HAS_MATPLOTLIB:
            print("[WARN] matplotlib yüklü değil, grafik üretilemiyor.")
            return

        os.makedirs(output_dir, exist_ok=True)
        speedup_data = self.get_speedup_data()

        fig, ax = plt.subplots(figsize=(10, 6))
        for problem, threads_data in speedup_data.items():
            threads = sorted(threads_data.keys())
            speedups = [threads_data[t]['speedup'] for t in threads]
            ax.plot(threads, speedups, 'o-', label=problem, linewidth=2,
                    markersize=8)

        # İdeal speedup çizgisi
        if speedup_data:
            max_threads = max(
                max(td.keys()) for td in speedup_data.values()
            )
            ideal = list(range(1, max_threads + 1))
            ax.plot(ideal, ideal, 'k--', alpha=0.5, label='İdeal Speedup')

        ax.set_xlabel('Thread Sayısı', fontsize=12)
        ax.set_ylabel('Speedup (S = T_seri / T_paralel)', fontsize=12)
        ax.set_title('Paralel Performans: Speedup Analizi', fontsize=14)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'speedup.png'), dpi=150)
        plt.close()

    def plot_efficiency(self, output_dir: str = 'plots'):
        """Efficiency grafiği"""
        if not HAS_MATPLOTLIB:
            return

        os.makedirs(output_dir, exist_ok=True)
        speedup_data = self.get_speedup_data()

        fig, ax = plt.subplots(figsize=(10, 6))
        for problem, threads_data in speedup_data.items():
            threads = sorted(threads_data.keys())
            effs = [threads_data[t]['efficiency'] for t in threads]
            ax.plot(threads, effs, 's--', label=problem, linewidth=2,
                    markersize=8)

        ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5,
                   label='İdeal Efficiency')
        ax.set_xlabel('Thread Sayısı', fontsize=12)
        ax.set_ylabel('Efficiency (E = S / P)', fontsize=12)
        ax.set_title('Paralel Performans: Efficiency Analizi', fontsize=14)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.5)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'efficiency.png'), dpi=150)
        plt.close()

    def plot_solver_comparison(self, output_dir: str = 'plots'):
        """Solver karsilastirma bar chart"""
        if not HAS_MATPLOTLIB:
            return

        os.makedirs(output_dir, exist_ok=True)

        # Problem x solver -> time dict
        solver_problem_times = defaultdict(dict)
        problems = []
        solvers_seen = set()
        for r in self.results:
            if r['num_threads'] <= 1 or r['solver'] == 'BruteForce':
                p = r['problem']
                s = r['solver']
                if p not in problems:
                    problems.append(p)
                solvers_seen.add(s)
                solver_problem_times[s][p] = r['time']

        if not problems or not solvers_seen:
            return

        solvers = sorted(solvers_seen)
        fig, ax = plt.subplots(figsize=(14, 6))
        x = np.arange(len(problems))
        width = 0.8 / len(solvers)
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']

        for i, solver in enumerate(solvers):
            times = [solver_problem_times[solver].get(p, 0) for p in problems]
            offset = (i - len(solvers) / 2 + 0.5) * width
            ax.bar(x + offset, times, width, label=solver,
                   color=colors[i % len(colors)], alpha=0.85)

        ax.set_xlabel('Problem', fontsize=12)
        ax.set_ylabel('Sure (saniye)', fontsize=12)
        ax.set_title('Solver Karsilastirmasi', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(problems, rotation=45, ha='right', fontsize=9)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'solver_comparison.png'), dpi=150)
        plt.close()

    def plot_time_vs_size(self, output_dir: str = 'plots'):
        """Problem boyutu vs Süre scatter plot"""
        if not HAS_MATPLOTLIB:
            return

        os.makedirs(output_dir, exist_ok=True)

        fig, ax = plt.subplots(figsize=(10, 6))
        solver_data = defaultdict(lambda: {'vars': [], 'times': []})
        for r in self.results:
            if r['num_threads'] <= 1 or r['solver'] == 'BruteForce':
                solver_data[r['solver']]['vars'].append(r['num_vars'])
                solver_data[r['solver']]['times'].append(r['time'])

        markers = ['o', 's', '^', 'D', 'v']
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
        for i, (solver, data) in enumerate(solver_data.items()):
            ax.scatter(data['vars'], data['times'],
                       marker=markers[i % len(markers)],
                       color=colors[i % len(colors)],
                       s=80, label=solver, alpha=0.8)

        ax.set_xlabel('Değişken Sayısı', fontsize=12)
        ax.set_ylabel('Süre (saniye)', fontsize=12)
        ax.set_title('Problem Boyutu vs Çözüm Süresi', fontsize=14)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'time_vs_size.png'), dpi=150)
        plt.close()

    def plot_heatmap(self, output_dir: str = 'plots'):
        """Heatmap: problem boyutu × thread sayısı → süre"""
        if not HAS_MATPLOTLIB:
            return

        os.makedirs(output_dir, exist_ok=True)

        # Paralel sonuçlardan veri topla
        problems = []
        thread_counts = set()
        time_data = {}

        for r in self.results:
            if r['solver'].startswith('ParallelBF'):
                p = r['problem']
                t = r['num_threads']
                if p not in problems:
                    problems.append(p)
                thread_counts.add(t)
                time_data[(p, t)] = r['time']

        if not problems or not thread_counts:
            return

        thread_counts = sorted(thread_counts)
        matrix = np.zeros((len(problems), len(thread_counts)))

        for i, p in enumerate(problems):
            for j, t in enumerate(thread_counts):
                matrix[i, j] = time_data.get((p, t), 0)

        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
        ax.set_xticks(range(len(thread_counts)))
        ax.set_xticklabels([str(t) for t in thread_counts])
        ax.set_yticks(range(len(problems)))
        ax.set_yticklabels(problems, fontsize=9)
        ax.set_xlabel('Thread Sayısı', fontsize=12)
        ax.set_ylabel('Problem', fontsize=12)
        ax.set_title('Heatmap: Problem × Thread → Süre (saniye)', fontsize=14)

        # Değerleri hücrelere yaz
        for i in range(len(problems)):
            for j in range(len(thread_counts)):
                val = matrix[i, j]
                color = 'white' if val > matrix.max() * 0.6 else 'black'
                ax.text(j, i, f'{val:.4f}', ha='center', va='center',
                        color=color, fontsize=8)

        plt.colorbar(im, label='Süre (saniye)')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'heatmap.png'), dpi=150)
        plt.close()

    def generate_all_plots(self, output_dir: str = 'plots'):
        """Tüm grafikleri oluşturur."""
        self.plot_speedup(output_dir)
        self.plot_efficiency(output_dir)
        self.plot_solver_comparison(output_dir)
        self.plot_time_vs_size(output_dir)
        self.plot_heatmap(output_dir)
        print(f"[OK] Tüm grafikler '{output_dir}/' klasörüne kaydedildi.")

    def save_metrics(self, filename: str = 'results/metrics.json'):
        """Tüm metrikleri JSON olarak kaydeder."""
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        speedup_data = self.get_speedup_data()

        metrics = {
            'speedup_data': {},
            'raw_results': self.results
        }

        for problem, td in speedup_data.items():
            metrics['speedup_data'][problem] = {
                str(t): {
                    'speedup': round(d['speedup'], 4),
                    'efficiency': round(d['efficiency'], 4),
                    'serial_time': round(d['serial_time'], 6),
                    'parallel_time': round(d['parallel_time'], 6)
                } for t, d in td.items()
            }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
