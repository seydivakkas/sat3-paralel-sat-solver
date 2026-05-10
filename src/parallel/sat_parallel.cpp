/*
 * SAT3 Paralel Programlama Projesi - OpenMP C++ Solver
 * =====================================================
 * Ogrenci: 416404 Seydi Vakkas Eryilmaz
 *
 * Derleme: g++ -fopenmp -O3 -std=c++17 sat_parallel.cpp -o sat_solver
 * Kullanim: ./sat_solver <dosya.cnf> [thread_sayisi]
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <cstdlib>
#include <cmath>
#include <chrono>
#include <optional>
#include <iomanip>

#ifdef _OPENMP
#include <omp.h>
#endif

using namespace std;

// ============================================================
// DIMACS Parser
// ============================================================
struct SATInstance {
    int num_vars;
    int num_clauses;
    vector<vector<int>> clauses;
};

SATInstance parse_dimacs(const string& filename) {
    SATInstance inst;
    inst.num_vars = 0;
    inst.num_clauses = 0;

    ifstream file(filename);
    if (!file.is_open()) {
        cerr << "HATA: Dosya acilamadi: " << filename << endl;
        exit(1);
    }

    string line;
    while (getline(file, line)) {
        if (line.empty() || line[0] == 'c' || line[0] == '%') continue;

        if (line.substr(0, 5) == "p cnf") {
            sscanf(line.c_str(), "p cnf %d %d", &inst.num_vars, &inst.num_clauses);
            continue;
        }

        vector<int> clause;
        int lit;
        stringstream ss(line);
        while (ss >> lit && lit != 0) {
            clause.push_back(lit);
        }
        if (!clause.empty()) {
            inst.clauses.push_back(clause);
        }
    }

    inst.num_clauses = (int)inst.clauses.size();
    return inst;
}

// ============================================================
// Clause / Formula Checker
// ============================================================
bool check_clause(const vector<int>& clause, const vector<bool>& assignment) {
    for (int lit : clause) {
        int var = abs(lit) - 1;
        bool val = assignment[var];
        if ((lit > 0 && val) || (lit < 0 && !val)) {
            return true;
        }
    }
    return false;
}

bool check_formula(const SATInstance& inst, const vector<bool>& assignment) {
    for (const auto& clause : inst.clauses) {
        if (!check_clause(clause, assignment)) {
            return false;
        }
    }
    return true;
}

// ============================================================
// Seri Brute Force
// ============================================================
struct SolverResult {
    bool satisfiable;
    vector<bool> assignment;
    double elapsed_seconds;
    long long combinations_tested;
};

SolverResult serial_bruteforce(const SATInstance& inst) {
    int n = inst.num_vars;
    long long total = 1LL << n;

    auto start = chrono::high_resolution_clock::now();

    for (long long i = 0; i < total; ++i) {
        vector<bool> assignment(n);
        for (int j = 0; j < n; ++j) {
            assignment[j] = (i >> j) & 1;
        }

        if (check_formula(inst, assignment)) {
            auto end = chrono::high_resolution_clock::now();
            double elapsed = chrono::duration<double>(end - start).count();
            return {true, assignment, elapsed, i + 1};
        }
    }

    auto end = chrono::high_resolution_clock::now();
    double elapsed = chrono::duration<double>(end - start).count();
    return {false, {}, elapsed, total};
}

// ============================================================
// Paralel Brute Force (OpenMP)
// ============================================================
SolverResult parallel_bruteforce(const SATInstance& inst, int num_threads) {
    int n = inst.num_vars;
    long long total = 1LL << n;
    bool found = false;
    vector<bool> solution;
    int solving_thread = -1;

    auto start = chrono::high_resolution_clock::now();

    #pragma omp parallel num_threads(num_threads) shared(found, solution, solving_thread)
    {
        #ifdef _OPENMP
        int tid = omp_get_thread_num();
        int nthreads = omp_get_num_threads();
        #else
        int tid = 0;
        int nthreads = 1;
        #endif

        long long chunk = total / nthreads;
        long long s = tid * chunk;
        long long e = (tid == nthreads - 1) ? total : s + chunk;

        for (long long i = s; i < e; ++i) {
            if (found) break;

            vector<bool> assignment(n);
            for (int j = 0; j < n; ++j) {
                assignment[j] = (i >> j) & 1;
            }

            if (check_formula(inst, assignment)) {
                #pragma omp critical
                {
                    if (!found) {
                        found = true;
                        solution = assignment;
                        solving_thread = tid;
                    }
                }
                break;
            }
        }
    }

    auto end = chrono::high_resolution_clock::now();
    double elapsed = chrono::duration<double>(end - start).count();

    if (found) {
        return {true, solution, elapsed, -1};
    }
    return {false, {}, elapsed, total};
}

// ============================================================
// Model yazdirma
// ============================================================
void print_model(const SATInstance& inst, const vector<bool>& assignment) {
    cout << "  Model: ";
    int limit = min((int)assignment.size(), 20);
    for (int i = 0; i < limit; ++i) {
        if (assignment[i]) {
            cout << (i + 1) << " ";
        } else {
            cout << -(i + 1) << " ";
        }
    }
    if ((int)assignment.size() > 20) {
        cout << "... (+" << (assignment.size() - 20) << " more)";
    }
    cout << endl;
}

// ============================================================
// Performans Analizi
// ============================================================
void run_performance_analysis(const SATInstance& inst, const string& filename) {
    cout << "\n========================================" << endl;
    cout << "  PERFORMANS ANALIZI: " << filename << endl;
    cout << "  Degisken: " << inst.num_vars
         << " | Clause: " << inst.num_clauses << endl;
    cout << "========================================" << endl;

    // Seri
    cout << "\n  [SERI] Brute Force..." << endl;
    SolverResult serial = serial_bruteforce(inst);
    cout << "  Durum: " << (serial.satisfiable ? "SAT" : "UNSAT")
         << " | Sure: " << fixed << setprecision(6) << serial.elapsed_seconds << "s" << endl;
    if (serial.satisfiable) {
        print_model(inst, serial.assignment);
    }

    double serial_time = serial.elapsed_seconds;

    // Paralel: 1, 2, 4, 8 thread
    int thread_counts[] = {1, 2, 4, 8};

    cout << "\n  " << setw(10) << left << "Threads"
         << setw(14) << left << "Sure (s)"
         << setw(12) << left << "Speedup"
         << setw(12) << left << "Efficiency"
         << endl;
    cout << "  " << string(48, '-') << endl;

    for (int t : thread_counts) {
        SolverResult par = parallel_bruteforce(inst, t);
        double speedup = (par.elapsed_seconds > 0) ?
                          serial_time / par.elapsed_seconds : 0;
        double efficiency = (t > 0) ? speedup / t : 0;

        cout << "  " << setw(10) << left << t
             << setw(14) << left << fixed << setprecision(6) << par.elapsed_seconds
             << setw(12) << left << fixed << setprecision(4) << speedup
             << setw(12) << left << fixed << setprecision(4) << efficiency
             << endl;
    }
}

// ============================================================
// Main
// ============================================================
int main(int argc, char* argv[]) {
    if (argc < 2) {
        cerr << "Kullanim: " << argv[0] << " <dosya.cnf> [thread_sayisi]" << endl;
        cerr << "  veya:   " << argv[0] << " --benchmark <dosya.cnf>" << endl;
        return 1;
    }

    string arg1 = argv[1];

    // Benchmark modu
    if (arg1 == "--benchmark" && argc >= 3) {
        string filename = argv[2];
        SATInstance inst = parse_dimacs(filename);
        run_performance_analysis(inst, filename);
        return 0;
    }

    // Normal mod
    string filename = arg1;
    #ifdef _OPENMP
    int num_threads = (argc >= 3) ? atoi(argv[2]) : omp_get_max_threads();
    #else
    int num_threads = (argc >= 3) ? atoi(argv[2]) : 1;
    #endif

    SATInstance inst = parse_dimacs(filename);

    cout << "Dosya: " << filename << endl;
    cout << "Degisken: " << inst.num_vars
         << " | Clause: " << inst.num_clauses
         << " | Thread: " << num_threads << endl;

    // Seri coz
    cout << "\n[SERI] Brute Force..." << endl;
    SolverResult serial = serial_bruteforce(inst);
    cout << "Durum: " << (serial.satisfiable ? "SAT" : "UNSAT")
         << " | Sure: " << fixed << setprecision(6) << serial.elapsed_seconds << "s" << endl;
    if (serial.satisfiable) print_model(inst, serial.assignment);

    // Paralel coz
    cout << "\n[PARALEL] OpenMP (" << num_threads << " thread)..." << endl;
    SolverResult par = parallel_bruteforce(inst, num_threads);
    cout << "Durum: " << (par.satisfiable ? "SAT" : "UNSAT")
         << " | Sure: " << fixed << setprecision(6) << par.elapsed_seconds << "s" << endl;
    if (par.satisfiable) print_model(inst, par.assignment);

    // Speedup
    if (serial.elapsed_seconds > 0 && par.elapsed_seconds > 0) {
        double speedup = serial.elapsed_seconds / par.elapsed_seconds;
        double efficiency = speedup / num_threads;
        cout << "\nSpeedup  : " << fixed << setprecision(4) << speedup << "x" << endl;
        cout << "Efficiency: " << fixed << setprecision(4) << efficiency << endl;
    }

    return 0;
}
