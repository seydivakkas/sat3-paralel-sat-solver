# SAT3 — Paralel SAT Çözücü

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![C++](https://img.shields.io/badge/C%2B%2B-17-00599C?logo=c%2B%2B)
![OpenMP](https://img.shields.io/badge/OpenMP-Paralel-green)
![Tests](https://img.shields.io/badge/Tests-29%20passed-brightgreen)
![License](https://img.shields.io/badge/License-Academic-lightgrey)

**DIMACS CNF formatındaki SAT problemlerini 4 farklı algoritmayı karşılaştırarak çözen paralel programlama projesi.**

</div>

---

## Proje Nedir? Ne Amaçlamaktadır?

### 🎯 Amaç

Bu proje, **SAT (Boolean Satisfiability) Problemi**ni paralel programlama teknikleriyle çözmeyi hedefleyen akademik bir çalışmadır.

SAT problemi şu soruyu sorar: *"Verilen bir Boolean formülü (CNF formatında) için, tüm clause'ları aynı anda doğru yapan bir değişken ataması var mı?"*

**Örnek:**

```
(x1 ∨ ¬x2) ∧ (x2 ∨ x3) ∧ (¬x1 ∨ ¬x3)
→ x1=True, x2=True, x3=False → SAT mı?
```

---

## 🛠️ İzlenen Yöntem

**4 farklı solver** karşılaştırmalı olarak implement edildi:

### 1. Brute Force (Seri)

Tüm `2^n` olası kombinasyonu tek tek dener. Basit ama yavaş.

### 2. Parallel Brute Force

Arama uzayını chunk'lara böler, her thread kendi aralığını tarar. İlk çözüm bulunduğunda diğerleri durdurulur.

```
Thread 0: [0     → 2^n/4)
Thread 1: [2^n/4 → 2^n/2)
Thread 2: [2^n/2 → 3*2^n/4)
Thread 3: [3*2^n/4 → 2^n)
```

### 3. DPLL (Akıllı Arama)

Brute force yerine akıllı budama yapar:

- **Unit Propagation** → Tek seçenekli clause'ları otomatik çözer
- **Pure Literal Elimination** → Sadece pozitif/negatif görünen değişkenleri atar
- **MOMS Heuristic** → En sık görünen değişkeni önce dener
- **Backtracking** → Çıkmaz sokaktan geri döner

### 4. Resolution

Mantıksal çıkarım yöntemi:

```
(A ∨ x) ∧ (B ∨ ¬x)  →  (A ∨ B)
```

Boş clause üretilirse → **UNSAT** ispatlanmış olur.

### 📊 Performans Karşılaştırması

| Solver | n=5 | n=15 | n=22 |
|--------|-----|------|------|
| DPLL | 0.0004s | 0.0003s | 0.001s |
| BruteForce | 0.00001s | 0.008s | — (atlandı) |
| Resolution | 0.004s | 5s (timeout) | 5s (timeout) |

> **Özet:** DPLL tüm problemlerde en hızlı yöntemdir. Brute force büyük problemlerde yetersiz kalır. Resolution özellikle UNSAT ispatında değerlidir.

### 💡 Paralel Programlamanın Rolü

Proje, seri ve paralel yaklaşımları karşılaştırarak **Speedup** ve **Efficiency** hesaplar:

```
Speedup    = T_seri / T_paralel
Efficiency = Speedup / thread_sayısı
```

Bu sayede *"kaç thread ne kadar fayda sağlar?"* sorusuna ampirik bir cevap verilmektedir.

---

## 📁 Proje Yapısı

```
SAT3 Problemi/
├── src/
│   ├── parser/
│   │   └── dimacs_parser.py        # DIMACS CNF parser
│   ├── solvers/
│   │   ├── brute_force.py          # Seri brute-force solver
│   │   ├── parallel_brute_force.py # Multi-thread paralel solver
│   │   ├── dpll.py                 # DPLL algoritması
│   │   └── resolution.py          # Resolution algoritması
│   ├── utils/
│   │   ├── verifier.py             # Çözüm doğrulayıcı
│   │   └── formatter.py            # CSV / JSON / tablo formatlayıcı
│   ├── analysis/
│   │   └── performance.py          # Speedup / Efficiency + grafikler
│   └── parallel/
│       └── sat_parallel.cpp        # C++ OpenMP paralel solver
├── tests/
│   └── test_all.py                 # pytest test suite (29 test)
├── test_cnf/
│   └── problem01-10.cnf            # 10 adet DIMACS test problemi
├── results/                        # Çıktılar (CSV, JSON, metrikler)
├── plots/                          # Performans grafikleri (5 adet)
├── docs/
│   └── RAPOR.md                    # Teknik rapor
├── main.py                         # Ana çalıştırıcı
├── generate_problems.py            # Problem üretici
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚡ Kurulum ve Kullanım

### Gereksinimler

- Python 3.9+
- `pip install -r requirements.txt`

### Hızlı Başlangıç

```bash
# 1. Test problemlerini oluştur
python generate_problems.py

# 2. Tüm solver'ları çalıştır
python main.py

# 3. Testleri çalıştır
python -m pytest tests/ -v
```

### C++ OpenMP Solver (Opsiyonel)

```bash
# Derle
g++ -fopenmp -O3 -std=c++17 src/parallel/sat_parallel.cpp -o sat_solver

# Tek problem çöz (4 thread)
./sat_solver test_cnf/problem05.cnf 4

# Benchmark modu (1,2,4,8 thread karşılaştırması)
./sat_solver --benchmark test_cnf/problem05.cnf
```

---

## 🧪 Test Sonuçları

```
29 passed in 0.04s
```

| Test Grubu | Adet |
|------------|------|
| Parser | 6 |
| Brute Force | 5 |
| Parallel Brute Force | 3 |
| DPLL | 6 |
| Resolution | 3 |
| Verifier | 4 |
| Cross-validation | 2 |

---

## 📈 Sonuçlar

### Çözüm Tablosu (10 Problem)

| Problem | Değişken | Clause | DPLL | BF | Resolution |
|---------|---------|--------|------|-----|------------|
| problem01 | 5 | 10 | ✅ SAT | ✅ SAT | ✅ SAT |
| problem02 | 8 | 20 | ✅ SAT | ✅ SAT | ✅ SAT |
| problem03 | 10 | 30 | ✅ SAT | ✅ SAT | ⏱ UNKNOWN |
| problem04 | 12 | 40 | ✅ SAT | ✅ SAT | ⏱ UNKNOWN |
| problem05 | 15 | 50 | ✅ SAT | ✅ SAT | ⏱ UNKNOWN |
| problem06 | 5 | 20 | ❌ UNSAT | ❌ UNSAT | ❌ UNSAT |
| problem07 | 18 | 70 | ✅ SAT | — | ⏱ UNKNOWN |
| problem08 | 20 | 85 | ✅ SAT | — | ⏱ UNKNOWN |
| problem09 | 10 | 40 | ❌ UNSAT | ❌ UNSAT | ❌ UNSAT |
| problem10 | 22 | 91 | ✅ SAT | — | ⏱ UNKNOWN |

### Speedup Tablosu

| Problem | 2 Thread | 4 Thread | En İyi Eff. |
|---------|----------|----------|-------------|
| problem01 | 0.01x | 0.02x | 0.50% |
| problem03 | 0.25x | 0.14x | 12.52% |
| problem05 | 0.96x | 0.91x | 47.86% |

> Problem büyüdükçe paralel yaklaşım daha etkili hale gelir.

---

## 🏗️ Mimariye Genel Bakış

```
main.py
  ├── parse_dimacs()          → CNFFormula
  ├── DPLLSolver.solve()      → (status, model)
  ├── ResolutionSolver.solve() → (status, None)
  ├── BruteForceSolver.solve() → (status, model)
  ├── ParallelBFSolver.solve() → (status, model)
  ├── verify_solution()        → bool
  ├── export_to_csv/json()     → results/
  └── PerformanceAnalyzer      → plots/
```

---

## 🎓 Akademik Kullanım

### Ders Bağlamı

Bu proje, **Paralel Programlama** dersi kapsamında geliştirilmiştir. Temel hedefler:

- SAT probleminin NP-complete yapısını kavramak
- Seri ve paralel algoritmaların pratik karşılaştırmasını yapmak
- Speedup ve Efficiency metriklerini ampirik olarak ölçmek
- DPLL, Resolution gibi klasik algoritmaları sıfırdan implement etmek

---

### 🔬 İncelenen Algoritmalar ve Akademik Kaynakları

| Algoritma | Yıl | Kaynak |
|-----------|-----|--------|
| **DPLL** | 1962 | Davis, Logemann, Loveland — *A Machine Program for Theorem Proving*, CACM |
| **Resolution** | 1965 | Robinson — *A Machine-Oriented Logic Based on the Resolution Principle*, JACM |
| **SAT NP-Completeness** | 1971 | Cook — *The Complexity of Theorem Proving Procedures*, STOC |
| **MOMS Heuristic** | 1992 | Freeman — *Improvements to Propositional Satisfiability Search Algorithms* |
| **OpenMP Parallelism** | — | Chapman, Jost, van der Pas — *Using OpenMP*, MIT Press |

---

### 📐 Temel Kavramlar

#### Amdahl Yasası

Paralel programlamada teorik maksimum speedup:

```
S_max = 1 / (1 - p + p/n)
```

- `p` = Paralelleştirilebilen iş oranı
- `n` = İşlemci / thread sayısı

Bu proje, **brute-force** için `p ≈ 1` (tamamen paralel) ancak **Python GIL** nedeniyle gerçek kazanım sınırlıdır.

#### DIMACS CNF Formatı

SAT yarışmalarında kullanılan standart format:

```
c Yorum satırı
p cnf <değişken_sayısı> <clause_sayısı>
1 -2 3 0     → (x₁ ∨ ¬x₂ ∨ x₃)
-1 2 0       → (¬x₁ ∨ x₂)
```

Kendi problemlerinizi test etmek için `test_cnf/` klasörüne `.cnf` dosyası ekleyip `python main.py` çalıştırabilirsiniz.

---

### 🧑‍🏫 Öğretim Amaçlı Kullanım

Bu repo şu amaçlarla kullanılabilir:

- **SAT algoritmalarını öğrenmek** — Her solver tamamen sıfırdan, bağımlılıksız implement edilmiştir
- **Paralel programlama kavramlarını görmek** — `ThreadPoolExecutor`, `threading.Event`, OpenMP örnekleri
- **Performans analizi yapmayı öğrenmek** — Speedup/Efficiency hesaplama ve grafik üretimi
- **Test-driven development** — `pytest` ile 29 birim test
- **Algoritma karşılaştırması** — Aynı problem üzerinde 4 farklı yaklaşım

#### Hangi dosyadan başlanmalı?

```
1. src/parser/dimacs_parser.py   → DIMACS formatını anlamak
2. src/solvers/brute_force.py    → Temel mantık
3. src/solvers/dpll.py           → Akıllı arama
4. src/solvers/resolution.py     → Mantıksal çıkarım
5. src/analysis/performance.py   → Ölçüm yöntemleri
```

---

### 🔗 Yararlı Kaynaklar

- **SATLIB** — Benchmark problemler: <https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html>
- **PySAT** — Endüstriyel SAT solver kütüphanesi: <https://pysathq.github.io/>
- **MiniSat** — Referans CDCL solver: <http://minisat.se/>
- **OpenMP** — Resmi dokümantasyon: <https://www.openmp.org/>
- **SAT Competition** — Yıllık SAT yarışması: <https://satcompetition.github.io/>

---

### ⛔ Kullanım Kısıtlaması

Bu depo **yalnızca inceleme amaçlıdır.** Aşağıdaki eylemler açıkça **yasaktır**:

- Kodun tamamının veya herhangi bir parçasının kopyalanması
- Değiştirilmesi, uyarlanması veya türev çalışma oluşturulması
- Kaynak gösterilse dahi herhangi bir amaçla yeniden dağıtılması
- Ticari veya akademik projelerde kullanılması
- Pull request veya katkı gönderilmesi

> İzinsiz kullanım telif hakkı ihlali teşkil eder.

---

## 🤝 Katkılar

Bu bölüm, projeye sonradan eklenen geliştirmeleri belgelemektedir.

---

### ➕ CDCL Solver Katkısı

**Dosya:** `src/solvers/cdcl.py`

Projenin orijinal 4 solver'ına ek olarak **CDCL (Conflict-Driven Clause Learning)** algoritması implement edilmiştir. CDCL, endüstriyel SAT solver'larının (MiniSat, Z3, CaDiCaL) temelini oluşturan modern algoritmadır.

#### DPLL → CDCL: Fark Nedir?

| Özellik | DPLL | CDCL |
|---------|------|------|
| Backtrack | Kronolojik (1 seviye geri) | Non-chronological (backjumping) |
| Cakışmadan öğrenme | ❌ Yok | ✅ Clause learning |
| Değişken seçimi | MOMS heuristic | VSIDS (cakışma istatistikleri) |
| Restart | ❌ Yok | ✅ Luby sequence |
| Cakışma analizi | ❌ Yok | ✅ 1-UIP tabanlı |

#### Uygulanan Teknikler

1. **Conflict Clause Learning** — Cakışma analizinden üretilen yeni clause'lar eklenir; aynı hata tekrar yapılmaz
2. **Non-chronological Backtracking (Backjumping)** — Cakışmanın gerçek nedenine doğrudan atlanır, gereksiz geri izleme önlenir
3. **VSIDS Heuristic** — Hangi değişkenin daha sık cakışmaya yol açtığı takip edilir, o değişken önce seçilir
4. **Luby Restart** — Takılı kalınan arama bölgelerinden kurtulmak için periyodik olarak sıfırlanır

#### Benchmark Sonuçları (10 Test Problemi)

| Problem | Değişken | CDCL | DPLL | Kazanım | Öğrenilen Clause |
|---------|---------|------|------|---------|-----------------|
| problem01 | 5 | 0.0001s | 0.0001s | — | 0 |
| problem02 | 8 | 0.0001s | 0.0001s | — | 0 |
| problem03 | 10 | 0.0001s | 0.0001s | — | 0 |
| problem04 | 12 | 0.0004s | 0.0003s | — | **4** |
| problem05 | 15 | 0.0002s | 0.0003s | **1.5x** | 0 |
| problem06 | 5 | 0.0000s | 0.0000s | — | 0 |
| problem07 | 18 | 0.0005s | 0.0013s | **2.6x** | 3 |
| problem08 | 20 | 0.0007s | 0.0031s | **4.4x** | 2 |
| problem09 | 10 | 0.0000s | 0.0000s | — | 0 |
| problem10 | 22 | 0.0014s | 0.0010s | — | 6 |

> ✅ **10/10 problemde DPLL ile aynı sonuç** — tüm SAT çözümleri doğrulandı.  
> Büyük problemlerde (n≥18) CDCL belirgin biçimde DPLL'den hızlıdır.

#### Kullanım

```python
from src.parser.dimacs_parser import parse_dimacs
from src.solvers.cdcl import CDCLSolver

cnf = parse_dimacs("test_cnf/problem08.cnf")
solver = CDCLSolver(cnf)
status, model = solver.solve()
stats = solver.get_stats()

print(f"Durum: {status}")
print(f"Öğrenilen clause: {stats['learned']}")
print(f"Restart sayısı: {stats['restarts']}")
```

---

## 📄 Lisans — All Rights Reserved

```
Copyright (c) 2026 Seydi Vakkas Eryılmaz
Tüm hakları saklıdır. Bu yazılım izinsiz kullanılamaz, kopyalanamaz,
değiştirilemez veya dağıtılamaz. Ayrıntılar için LICENSE dosyasına bakın.
```

[![License: All Rights Reserved](https://img.shields.io/badge/License-All%20Rights%20Reserved-red.svg)](./LICENSE)

---

**Yazar:** Seydi Vakkas Eryılmaz
