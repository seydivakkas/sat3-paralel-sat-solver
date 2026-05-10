"""
Result Formatter
================
SAT çözüm sonuçlarını CSV, JSON ve okunabilir formatta çıktılar.
"""

import csv
import json
import os
from typing import List, Dict, Optional
from datetime import datetime


def format_model_string(model: Optional[Dict[int, bool]],
                        max_vars: int = 20) -> str:
    """Model'i okunabilir string'e çevirir. İlk max_vars değişkeni gösterir."""
    if model is None:
        return "N/A"
    sorted_vars = sorted(model.keys())[:max_vars]
    parts = []
    for v in sorted_vars:
        val = model[v]
        parts.append(f"{v}" if val else f"-{v}")
    result = " ".join(parts)
    if len(model) > max_vars:
        result += f" ... (+{len(model) - max_vars} more)"
    return result


def print_readable_solution(result: dict):
    """Tek bir çözümü terminale okunabilir şekilde yazdırır."""
    print(f"  Problem : {result.get('problem', 'N/A')}")
    print(f"  Solver  : {result.get('solver', 'N/A')}")
    print(f"  Durum   : {result.get('status', 'N/A')}")
    print(f"  Süre    : {result.get('time', 0):.6f} saniye")
    if result.get('model'):
        print(f"  Model   : {format_model_string(result['model'])}")
    if result.get('stats'):
        for k, v in result['stats'].items():
            if k not in ('time', 'status'):
                print(f"  {k}: {v}")
    print()


def export_to_csv(results: List[dict], filename: str):
    """Sonuçları CSV dosyasına yazar."""
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)

    fieldnames = ['problem', 'solver', 'status', 'time',
                  'num_vars', 'num_clauses', 'first_20_vars']

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                'problem': r.get('problem', ''),
                'solver': r.get('solver', ''),
                'status': r.get('status', ''),
                'time': f"{r.get('time', 0):.6f}",
                'num_vars': r.get('num_vars', ''),
                'num_clauses': r.get('num_clauses', ''),
                'first_20_vars': format_model_string(r.get('model'), 20)
            })


def export_to_json(results: List[dict], filename: str):
    """Sonuçları JSON dosyasına yazar."""
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)

    output = {
        'timestamp': datetime.now().isoformat(),
        'total_problems': len(results),
        'results': []
    }

    for r in results:
        entry = {
            'problem': r.get('problem', ''),
            'solver': r.get('solver', ''),
            'status': r.get('status', ''),
            'time': r.get('time', 0),
            'num_vars': r.get('num_vars', 0),
            'num_clauses': r.get('num_clauses', 0),
        }
        if r.get('model'):
            # Model'i literal listesine çevir
            model = r['model']
            entry['solution'] = {
                f"x{k}": v for k, v in sorted(model.items())
            }
            sorted_vars = sorted(model.keys())[:20]
            entry['first_20_vars'] = [
                k if model[k] else -k for k in sorted_vars
            ]
        if r.get('stats'):
            entry['stats'] = {
                k: v for k, v in r['stats'].items()
                if k not in ('time', 'status')
            }
        output['results'].append(entry)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def generate_summary_table(results: List[dict]) -> str:
    """Sonuçları tablo formatında string olarak döndürür."""
    try:
        from tabulate import tabulate
        headers = ['Problem', 'Solver', 'Durum', 'Süre (s)',
                   'Değişken', 'Clause', 'İlk 20 Değişken']
        rows = []
        for r in results:
            rows.append([
                r.get('problem', ''),
                r.get('solver', ''),
                r.get('status', ''),
                f"{r.get('time', 0):.6f}",
                r.get('num_vars', ''),
                r.get('num_clauses', ''),
                format_model_string(r.get('model'), 10)
            ])
        return tabulate(rows, headers=headers, tablefmt='grid')
    except ImportError:
        # Fallback: basit tablo
        lines = []
        lines.append(f"{'Problem':<15} {'Solver':<20} {'Durum':<8} {'Süre (s)':<12}")
        lines.append("-" * 60)
        for r in results:
            lines.append(
                f"{r.get('problem', ''):<15} "
                f"{r.get('solver', ''):<20} "
                f"{r.get('status', ''):<8} "
                f"{r.get('time', 0):<12.6f}"
            )
        return "\n".join(lines)
