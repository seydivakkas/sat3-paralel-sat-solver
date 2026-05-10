# SAT3 Paralel Programlama Projesi - Teknik Rapor

**Ogrenci No:** 416404  
**Ad Soyad:** Seydi Vakkas Eryilmaz  
**Tarih:** Mayis 2026  

---

## 1. Giris

### 1.1 SAT Problemi Tanimi

SAT (Boolean Satisfiability) problemi, verilen bir Boolean formulunun satisfiable (tatmin edilebilir) olup olmadigini belirleyen bir karar problemidir. Cook-Levin teoremine gore, SAT NP-complete sinifindadir ve bilgisayar bilimlerindeki en temel problemlerden biridir.

CNF (Conjunctive Normal Form) formatinda bir SAT problemi:

```
F = C1 ∧ C2 ∧ ... ∧ Cm
```

Her clause `Ci`, literallerin disjunction'idir:

```
Ci = (l1 ∨ l2 ∨ ... ∨ lk)
```

Bir literal `li`, bir degisken `xi` veya negasyonu `¬xi` olabilir.

### 1.2 Proje Amaci

Bu projenin amaci:
1. DIMACS CNF formatindaki SAT problemlerini **4 farkli yontemle** cozmek
2. **Paralel programlama** teknikleriyle brute-force cozumu hizlandirmak
3. Seri ve paralel cozumlerin **performans analizini** yapmak (Speedup, Efficiency)
4. Sonuclari **sistematik olarak** raporlamak

### 1.3 Kullanilan Yontemler

| Yontem | Tur | Karmasiklik | Aciklama |
|--------|-----|-------------|----------|
| Brute Force (Seri) | Tam Arama | O(2^n * m) | Tum kombinasyonlari dener |
| Parallel Brute Force | Paralel Arama | O(2^n * m / p) | Arama uzayini thread'lere boler |
| DPLL | Akilli Arama | Degisken | Unit Propagation + Backtracking |
| Resolution | Cikarim | Degisken | Clause birlestirme ile UNSAT ispatlar |

---

## 2. Yontemler

### 2.1 DIMACS CNF Formati

DIMACS CNF, SAT problemleri icin standart dosya formatidir:

```
c Yorum satiri
p cnf 3 4          # 3 degisken, 4 clause
1 2 -3 0           # (x1 ∨ x2 ∨ ¬x3)
-1 2 0             # (¬x1 ∨ x2)
1 -2 3 0           # (x1 ∨ ¬x2 ∨ x3)
-1 -2 -3 0         # (¬x1 ∨ ¬x2 ∨ ¬x3)
```

### 2.2 Brute Force Algoritmasi

**Pseudocode:**
```
function BRUTE_FORCE(clauses, n_vars):
    for i = 0 to 2^n - 1:
        assignment = int_to_binary(i, n_vars)
        if CHECK_FORMULA(clauses, assignment):
            return SAT, assignment
    return UNSAT, null
```

- Tum `2^n` olasi truth assignment'lari sirayla dener
- Her assignment icin tum clause'lari kontrol eder
- Ilk bulunan cozumu dondurur
- Kucuk problemler (n <= 15) icin pratiktir

### 2.3 Paralel Brute Force

**Yuk Dagitim Stratejisi (Static Chunking):**

```
Toplam is = 2^n
chunk_size = ceil(2^n / num_threads)

Thread 0: [0, chunk_size)
Thread 1: [chunk_size, 2*chunk_size)
...
Thread p-1: [(p-1)*chunk_size, 2^n)
```

**Pseudocode:**
```
function PARALLEL_BRUTE_FORCE(clauses, n_vars, p):
    chunks = divide_range(0, 2^n, p)
    found = Event()
    
    parallel for each chunk in chunks:
        for i in chunk:
            if found.is_set(): break
            assignment = int_to_binary(i, n_vars)
            if CHECK_FORMULA(clauses, assignment):
                found.set()
                return SAT, assignment
    
    return UNSAT, null
```

- `ThreadPoolExecutor` ile p adet thread olusturulur
- `threading.Event` ile early termination saglanir
- Ilk cozum bulan thread, diger thread'leri durdurur

### 2.4 DPLL Algoritmasi

DPLL (Davis-Putnam-Logemann-Loveland), geri izlemeli arama yapan tam (complete) bir SAT cozumleyicisidir.

**Pseudocode:**
```
function DPLL(clauses, assignment):
    // 1. Unit Propagation
    clauses, assignment = UNIT_PROPAGATION(clauses, assignment)
    if conflict: return null
    
    // 2. Pure Literal Elimination
    clauses, assignment = PURE_LITERAL_ELIM(clauses, assignment)
    
    // 3. Base Cases
    if clauses empty: return assignment  // SAT
    if empty clause exists: return null  // UNSAT
    
    // 4. Branching (MOMS heuristic)
    var = SELECT_VARIABLE(clauses)
    
    // True branch
    result = DPLL(simplify(clauses, var), assignment ∪ {var=True})
    if result != null: return result
    
    // False branch (backtrack)
    result = DPLL(simplify(clauses, -var), assignment ∪ {var=False})
    return result
```

**Alt Algoritmalar:**

1. **Unit Propagation:** Tek literal kalan clause'lardaki literal zorunlu olarak atanir
2. **Pure Literal Elimination:** Sadece pozitif veya negatif gorunen degiskenler atanir
3. **MOMS Heuristic:** En kucuk clause'larda en sik gorunen degisken secilir

### 2.5 Resolution Algoritmasi

**Resolution Kurali:**

```
(A ∨ x) ∧ (B ∨ ¬x) → (A ∨ B)
```

**Pseudocode:**
```
function RESOLUTION(clauses):
    S = set(clauses)
    while True:
        new_resolvents = {}
        for (C1, C2) in all_pairs(S):
            R = resolve(C1, C2)
            if R is empty: return UNSAT
            if R not in S: new_resolvents.add(R)
        
        if new_resolvents is empty: return SAT
        S = S ∪ new_resolvents
```

**Optimizasyonlar:**
- **Tautology Elimination:** `(x ∨ ¬x ∨ A)` seklindeki tautology'ler atilir
- **Subsumption:** `(A)` clause'u `(A ∨ B)`'yi subsume eder
- **Max Clause Size:** Belirli boyutun uzerindeki clause'lar atilir

---

## 3. Implementasyon Detaylari

### 3.1 Programlama Dilleri ve Kutuphaneler

**Python:**
- `concurrent.futures` - Thread pool paralelligi
- `threading` - Event-based senkronizasyon
- `matplotlib` - Performans grafikleri
- `numpy` - Sayisal islemler
- `pytest` - Test framework

**C++ (Opsiyonel):**
- OpenMP (`#pragma omp parallel`) - Shared-memory paralelligi
- STL containers - vector, set
- `chrono` - Yuksek cozunurluklu zaman olcumu

### 3.2 Mimari Diyagram

```
┌──────────────────────────────────────────────────┐
│                    main.py                        │
│    (Orkestrator - Tum solver'lari calistirir)     │
└────────────┬─────────────────────────────────────┘
             │
     ┌───────┴───────┐
     │               │
┌────┴────┐  ┌───────┴──────────┐
│ Parser  │  │    Solvers       │
│ (DIMACS)│  │ ┌──────────────┐ │
│         │  │ │ BruteForce   │ │
└─────────┘  │ │ ParallelBF   │ │
             │ │ DPLL         │ │
             │ │ Resolution   │ │
             │ └──────────────┘ │
             └───────┬──────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
   ┌──────┴──────┐   ┌─────────┴────────┐
   │   Utils     │   │   Analysis       │
   │ (Verifier,  │   │ (Performance,    │
   │  Formatter) │   │  Grafikler)      │
   └─────────────┘   └──────────────────┘
```

### 3.3 Load Balancing Stratejisi

**Static Chunking** kullanilmistir:
- Arama uzayi `2^n` esit parcaya bolunur
- Her thread kendine ait aralik uzerinde calisir
- `threading.Event` ile ilk cozum bulundugunda tum thread'ler durur

---

## 4. Test Problemleri

10 adet DIMACS CNF formatinda 3-SAT problemi olusturulmustur:

| # | Dosya | Degisken | Clause | Zorluk | Beklenen |
|---|-------|---------|--------|--------|----------|
| 1 | problem01.cnf | 5 | 10 | Cok Kolay | SAT |
| 2 | problem02.cnf | 8 | 20 | Kolay | SAT |
| 3 | problem03.cnf | 10 | 30 | Orta-Kolay | SAT |
| 4 | problem04.cnf | 12 | 40 | Orta | SAT |
| 5 | problem05.cnf | 15 | 50 | Orta-Zor | SAT |
| 6 | problem06.cnf | 5 | 20 | UNSAT | UNSAT |
| 7 | problem07.cnf | 18 | 70 | Zor | SAT |
| 8 | problem08.cnf | 20 | 85 | Cok Zor | SAT |
| 9 | problem09.cnf | 10 | 40 | UNSAT | UNSAT |
| 10 | problem10.cnf | 22 | 91 | En Zor | SAT |

---

## 5. Sonuclar

### 5.1 Cozum Tablosu

| Problem | DPLL Durumu | DPLL Sure (s) | BF Durumu | BF Sure (s) | Resolution |
|---------|------------|---------------|-----------|-------------|------------|
| problem01.cnf | SAT | 0.000445 | SAT | 0.000014 | SAT |
| problem02.cnf | SAT | 0.000104 | SAT | 0.000041 | SAT |
| problem03.cnf | SAT | 0.000156 | SAT | 0.000192 | UNKNOWN |
| problem04.cnf | SAT | 0.000319 | SAT | 0.000935 | UNKNOWN |
| problem05.cnf | SAT | 0.000322 | SAT | 0.008574 | UNKNOWN |
| problem06.cnf | UNSAT | 0.000007 | UNSAT | 0.000033 | UNSAT |
| problem07.cnf | SAT | 0.001245 | N/A | N/A | UNKNOWN |
| problem08.cnf | SAT | 0.001700 | N/A | N/A | UNKNOWN |
| problem09.cnf | UNSAT | 0.000010 | UNSAT | 0.001469 | UNSAT |
| problem10.cnf | SAT | 0.000983 | N/A | N/A | UNKNOWN |

### 5.2 Ilk 20 Degisken Degerleri

- **problem01:** x1=T, x2=T, x3=T, x4=T, x5=F
- **problem02:** x1=T, x2=T, x3=T, x4=T, x5=T, x6=T, x7=F, x8=T
- **problem05:** x1=F, x2=T, x3=T, x4=T, x5=T, x6=F, x7=T, x8=T, x9=T, x10=F, x11=T, x12=T, x13=T, x14=T, x15=T
- **problem06:** UNSAT (cozum yok)
- **problem09:** UNSAT (cozum yok)

### 5.3 Paralel Brute Force Speedup

| Problem | Threads | Seri (s) | Paralel (s) | Speedup | Efficiency |
|---------|---------|----------|-------------|---------|------------|
| problem01.cnf | 2 | 0.000014 | 0.001381 | 0.01x | 0.50% |
| problem01.cnf | 4 | 0.000014 | 0.000773 | 0.02x | 0.45% |
| problem02.cnf | 2 | 0.000041 | 0.000752 | 0.05x | 2.72% |
| problem02.cnf | 4 | 0.000041 | 0.000669 | 0.06x | 1.53% |
| problem03.cnf | 2 | 0.000192 | 0.000768 | 0.25x | 12.52% |
| problem03.cnf | 4 | 0.000192 | 0.001368 | 0.14x | 3.51% |
| problem04.cnf | 2 | 0.000935 | 0.001539 | 0.61x | 30.38% |
| problem04.cnf | 4 | 0.000935 | 0.001627 | 0.57x | 14.36% |
| problem05.cnf | 2 | 0.008574 | 0.008957 | 0.96x | 47.86% |
| problem05.cnf | 4 | 0.008574 | 0.009439 | 0.91x | 22.71% |

---

## 6. Performans Analizi

### 6.1 Speedup ve Efficiency Formulleri

**Speedup (Hizlanma):**

```
S = T_seri / T_paralel
```

- T_seri: Tek thread ile gecen sure
- T_paralel: p thread ile gecen sure
- Ideal durum: S = p (Linear Speedup)

**Efficiency (Verimlilik):**

```
E = S / p
```

- p: Islemci/thread sayisi
- Ideal durum: E = 1.0 (%100)

### 6.2 Analiz

**Gozlemler:**

1. **DPLL en hizli solver'dir** - Tum problemleri mikrosaniyeler icinde cozer
2. **Brute Force** kucuk problemlerde (n<=15) makul surelerde calisir
3. **Paralel BF Speedup < 1** - Kucuk problemlerde thread olusturma overhead'i hesaplama suresinden buyuktur
4. **Problem05 (n=15)** en iyi speedup'i gosterir (0.96x) cunku arama uzayi yeterince buyuktur
5. **Resolution** kucuk UNSAT problemlerde basarilidir, buyuk problemlerde timeout'a ugramistir

**Neden Speedup < 1?**

Python'da paralel brute-force'un seri'den yavas olmasi beklenen bir durumdur:
- **Python GIL:** CPython'daki Global Interpreter Lock, CPU-bound thread'lerin gercek paralelligini onler
- **Thread overhead:** Thread olusturma ve senkronizasyon maliyeti, kucuk problemlerdeki hesaplama suresinden fazladir
- **Arama uzayi kucuk:** n=5 icin sadece 32, n=15 icin 32768 kombinasyon var

**Gercek paralellik icin C++ OpenMP** gereklidir. C++ implementasyonunda OpenMP ile gercek shared-memory paralellik saglanmistir.

### 6.3 Solver Karsilastirmasi

| Solver | Avantaj | Dezavantaj |
|--------|---------|-----------|
| **DPLL** | En hizli, akilli budama | Implementasyon karmasikligi |
| **Brute Force** | Basit, anlasilir | n>20 icin yavas |
| **Parallel BF** | Buyuk arama uzayinda etkili | Thread overhead |
| **Resolution** | UNSAT ispati | Buyuk problemlerde cok fazla clause uretir |

---

## 7. Tartisma

### 7.1 Hangi Yontem Ne Zaman Iyi?

- **Kucuk SAT (n<15):** Brute Force yeterli
- **Orta SAT (15<n<50):** DPLL en iyi secim
- **Buyuk SAT (n>50):** CDCL (Conflict-Driven Clause Learning) gerekir
- **UNSAT ispati:** Resolution algoritmasi DPLL'den bagimsiz bir ispat saglar
- **Yuksek performans:** C++ + OpenMP ile gercek paralellik

### 7.2 Karsilasilan Zorluklar

1. **Windows multiprocessing:** Python'da `multiprocessing` modulu Windows'ta `spawn` kullanir, bu da buyuk overhead yaratir
2. **Resolution bellek kullanimi:** Resolvent sayisi karesel olarak buyuyebilir
3. **Python GIL:** CPU-bound islemlerde threading etkisiz kalir

### 7.3 Iyilestirme Onerileri

1. **CDCL implementasyonu:** Conflict-Driven Clause Learning ile daha buyuk problemler cozulebilir
2. **Cython/ctypes:** Python solver'larinin C extension olarak yazilmasi
3. **MPI destegi:** Dagitik bellek paraleligi ile coklu makine destegi
4. **VSIDS heuristic:** Degisken seciminde daha iyi heuristic'ler

---

## 8. Sonuc ve Gelecek Calismalar

Bu projede 4 farkli SAT solver basariyla implement edilmistir:

- **29 birim test** tamamiyla gecmektedir
- **10 farkli DIMACS problemi** cozulmustur (8 SAT, 2 UNSAT)
- **Performans analizi** yapilmis ve 5 grafik uretilmistir
- **C++ OpenMP** ile gercek paralel solver yazilmistir
- Tum solver'lar **cross-validation** ile dogrulanmistir

Gelecek calismalarda CDCL algoritmasi, MPI ile dagitik paralellik ve GPU-based SAT solver'lar arastirilabilir.

---

## 9. Kaynakca

1. Davis, M., Putnam, H. (1960). "A Computing Procedure for Quantification Theory." JACM.
2. Davis, M., Logemann, G., Loveland, D. (1962). "A Machine Program for Theorem Proving." CACM.
3. Cook, S. (1971). "The Complexity of Theorem Proving Procedures." STOC.
4. Biere, A., et al. (2009). "Handbook of Satisfiability." IOS Press.
5. SATLIB - Benchmark Problems: https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html
6. PySAT Documentation: https://pysathq.github.io/
7. OpenMP Specification: https://www.openmp.org/specifications/

---

## 10. Ekler

### 10.1 Proje Dosya Yapisi

```
SAT3 Problemi/
├── src/
│   ├── parser/dimacs_parser.py
│   ├── solvers/
│   │   ├── brute_force.py
│   │   ├── parallel_brute_force.py
│   │   ├── dpll.py
│   │   └── resolution.py
│   ├── utils/
│   │   ├── verifier.py
│   │   └── formatter.py
│   ├── analysis/performance.py
│   └── parallel/sat_parallel.cpp
├── tests/test_all.py
├── test_cnf/problem01-10.cnf
├── results/
│   ├── results.csv
│   ├── results.json
│   └── metrics.json
├── plots/
│   ├── speedup.png
│   ├── efficiency.png
│   ├── solver_comparison.png
│   ├── time_vs_size.png
│   └── heatmap.png
├── main.py
├── generate_problems.py
├── requirements.txt
└── README.md
```

### 10.2 Kurulum ve Calistirma

```bash
# Bagimliliklari kur
pip install -r requirements.txt

# Test problemlerini olustur
python generate_problems.py

# Tum solver'lari calistir
python main.py

# Testleri calistir
python -m pytest tests/ -v

# C++ solver derle ve calistir
g++ -fopenmp -O3 -std=c++17 src/parallel/sat_parallel.cpp -o sat_solver
./sat_solver test_cnf/problem05.cnf 4
```

### 10.3 Test Sonuclari

```
29 passed in 0.50s
```

Tum birim testler basariyla gecmistir:
- Parser testleri (6)
- Brute Force testleri (5)
- Parallel BF testleri (3)
- DPLL testleri (6)
- Resolution testleri (3)
- Verifier testleri (4)
- Cross-validation testleri (2)
