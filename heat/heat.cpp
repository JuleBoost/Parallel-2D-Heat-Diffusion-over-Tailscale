// 2D heat equation u_t = alpha (u_xx + u_yy) on [0,1]^2, explicit 5-point scheme (Task 5.2).
// --decomp serial : reference solver (Part 1)
// --decomp strips : 1D strip decomposition, rows split among ranks (Part 2)
// --decomp blocks : 2D block decomposition on a Cartesian process grid (Part 3)
#include <mpi.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>

struct Params {
    std::string cas = "1";      // 1, 2 or V
    int N = 128;                // intervals per direction
    double r = 0.2;             // alpha*dt/h^2
    double T = -1;              // final time (if > 0)
    long steps = -1;            // or fixed number of steps
    std::string out;            // output file (optional)
    std::string decomp = "serial";
    bool force = false;         // --force 1 : allow unstable r (only for Task 6.7)
    bool print = false;         // --print 1 : dump local arrays incl. ghosts (debugging)
};

static int g_rank = 0;

[[noreturn]] static void fail(const char* msg) {
    if (g_rank == 0) std::fprintf(stderr, "%s", msg);
    MPI_Finalize();
    std::exit(1);
}

static Params parse(int argc, char** argv) {
    const char* use =
        "usage: heat --case 1|2|V --N <int> --r <double> (--T <double> | --steps <int>)\n"
        "            [--out file.bin] [--decomp serial|strips|blocks]\n";
    Params p;
    for (int k = 1; k < argc; ++k) {
        std::string a = argv[k];
        if (k + 1 >= argc) fail(use);
        std::string v = argv[++k];
        if (a == "--case") p.cas = v;
        else if (a == "--N") p.N = std::atoi(v.c_str());
        else if (a == "--r") p.r = std::atof(v.c_str());
        else if (a == "--T") p.T = std::atof(v.c_str());
        else if (a == "--steps") p.steps = std::atol(v.c_str());
        else if (a == "--out") p.out = v;
        else if (a == "--decomp") p.decomp = v;
        else if (a == "--force") p.force = (v == "1");
        else if (a == "--print") p.print = (v == "1");
        else fail(use);
    }
    if (p.cas != "1" && p.cas != "2" && p.cas != "V") fail(use);
    if (p.decomp != "serial" && p.decomp != "strips" && p.decomp != "blocks") fail(use);
    if (p.N < 2) fail("error: N must be >= 2\n");
    if ((p.T > 0) == (p.steps > 0)) fail("error: give exactly one of --T or --steps\n");
    return p;
}

// Initial / boundary value at global node (i, j). Boundary values stay fixed (Dirichlet).
static double init_value(const std::string& cas, int N, int i, int j) {
    const double pi = std::acos(-1.0), h = 1.0 / N;
    bool edgeX = (i == 0 || i == N), edgeY = (j == 0 || j == N);
    if (cas == "1") return (edgeX || edgeY) ? 1.0 : 0.0;
    if (cas == "2") return edgeY ? 1.0 : 0.0;                 // top/bottom hot incl. corners
    return (edgeX || edgeY) ? 0.0 : std::sin(pi * i * h) * std::sin(pi * j * h);
}

// The update of one row. EXACTLY the same expression in every decomposition,
// so the results are bit-for-bit identical (background notes, Task 5.2(d)).
static inline void update_row(const double* dn, const double* c, const double* up,
                              double* o, int i0, int i1, double rr) {
    for (int i = i0; i <= i1; ++i)
        o[i] = c[i] + rr * (c[i - 1] + c[i + 1] + dn[i] + up[i] - 4.0 * c[i]);
}

// Split n interior nodes (global indices 1..n) among p parts; the first n%p get one extra.
static void split(int n, int p, int k, int& start, int& count) {
    int base = n / p, rem = n % p;
    count = base + (k < rem ? 1 : 0);
    start = 1 + k * base + std::min(k, rem);
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank, P;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &P);
    g_rank = rank;

    Params p = parse(argc, argv);
    const double alpha = 1.0, pi = std::acos(-1.0);
    const int N = p.N, n = N + 1;
    const double h = 1.0 / N;

    // Stability (Task 6.3): r = alpha*dt/h^2 <= 1/4 in 2D
    if (p.r <= 0 || (p.r > 0.25 && !p.force)) {
        char m[256];
        std::snprintf(m, sizeof m, "error: r = %g is unstable. The explicit 2D scheme needs "
                                   "0 < r <= 1/4 (von Neumann, Task 6.3).\n", p.r);
        fail(m);
    }
    double dt; long steps;
    if (p.T > 0) { steps = (long)std::ceil(p.T / (p.r * h * h / alpha) - 1e-9); dt = p.T / steps; }
    else         { steps = p.steps; dt = p.r * h * h / alpha; }
    const double rr = alpha * dt / (h * h);
    if (p.decomp == "serial" && P != 1) fail("error: --decomp serial must run with 1 process\n");

    // ---------------- process grid ----------------
    int Px = 1, Py = P, cx = 0, cy = rank;
    int down = MPI_PROC_NULL, up = MPI_PROC_NULL, left = MPI_PROC_NULL, right = MPI_PROC_NULL;
    MPI_Comm grid = MPI_COMM_WORLD, cart = MPI_COMM_NULL;
    if (p.decomp == "strips") {
        // rank 0 owns the bottom strip, rank P-1 the top one
        down = (rank > 0) ? rank - 1 : MPI_PROC_NULL;
        up   = (rank < P - 1) ? rank + 1 : MPI_PROC_NULL;
    } else if (p.decomp == "blocks") {
        int dims[2] = {0, 0}, periods[2] = {0, 0}, coords[2];
        MPI_Dims_create(P, 2, dims);
        Py = dims[0]; Px = dims[1];                    // dimension 0 = y (rows), 1 = x (columns)
        MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 0, &cart);
        grid = cart;
        MPI_Comm_rank(cart, &rank);
        MPI_Cart_coords(cart, rank, 2, coords);
        cy = coords[0]; cx = coords[1];
        MPI_Cart_shift(cart, 0, 1, &down, &up);        // edges of the plate -> MPI_PROC_NULL
        MPI_Cart_shift(cart, 1, 1, &left, &right);
    }
    if (N - 1 < Px || N - 1 < Py) fail("error: too many processes for this N\n");

    // my block of interior nodes: global i in [i0, i0+nx), j in [j0, j0+ny)
    int i0, nx, j0, ny;
    split(N - 1, Px, cx, i0, nx);
    split(N - 1, Py, cy, j0, ny);
    if (p.decomp == "serial") { i0 = 1; nx = N - 1; j0 = 1; ny = N - 1; }

    // local arrays with one ghost layer on each side: (ny+2) rows of (nx+2) values
    const int W = nx + 2;
    auto L = [W](int li, int lj) { return (size_t)lj * W + li; };
    std::vector<double> u((size_t)(ny + 2) * W), unew;
    for (int lj = 0; lj < ny + 2; ++lj)              // ghosts on the plate edge hold the
        for (int li = 0; li < W; ++li)               // (fixed) boundary values; the others
            u[L(li, lj)] = init_value(p.cas, N, i0 - 1 + li, j0 - 1 + lj);   // get overwritten
    unew = u;

    // column datatype for blocks: ny values with stride W (MPI_Type_vector, no manual packing)
    MPI_Datatype column;
    MPI_Type_vector(ny, 1, W, MPI_DOUBLE, &column);
    MPI_Type_commit(&column);

    // ---------------- time stepping ----------------
    double tcomm = 0.0, tcomp = 0.0;
    MPI_Barrier(grid);
    double t0 = MPI_Wtime();
    for (long s = 0; s < steps; ++s) {
        double ta = MPI_Wtime();
        if (p.decomp != "serial") {
            // rows: send top owned row up, receive bottom ghost from below; then the reverse.
            // Rows are contiguous: strips send the whole row (N+1 doubles, boundary columns
            // included), blocks send only their nx interior values (corners are not needed).
            const int i_row = (p.decomp == "strips") ? 0 : 1, n_row = (p.decomp == "strips") ? W : nx;
            MPI_Sendrecv(&u[L(i_row, ny)], n_row, MPI_DOUBLE, up, 0,
                         &u[L(i_row, 0)], n_row, MPI_DOUBLE, down, 0, grid, MPI_STATUS_IGNORE);
            MPI_Sendrecv(&u[L(i_row, 1)], n_row, MPI_DOUBLE, down, 1,
                         &u[L(i_row, ny + 1)], n_row, MPI_DOUBLE, up, 1, grid, MPI_STATUS_IGNORE);
            if (p.decomp == "blocks") {
                // columns: send right owned column right, receive left ghost; then the reverse
                MPI_Sendrecv(&u[L(nx, 1)], 1, column, right, 2,
                             &u[L(0, 1)], 1, column, left, 2, grid, MPI_STATUS_IGNORE);
                MPI_Sendrecv(&u[L(1, 1)], 1, column, left, 3,
                             &u[L(nx + 1, 1)], 1, column, right, 3, grid, MPI_STATUS_IGNORE);
            }
        }
        double tb = MPI_Wtime();
        for (int lj = 1; lj <= ny; ++lj)
            update_row(&u[L(0, lj - 1)], &u[L(0, lj)], &u[L(0, lj + 1)], &unew[L(0, lj)], 1, nx, rr);
        std::swap(u, unew);                            // swap, not copy
        double tc = MPI_Wtime();
        tcomm += tb - ta;
        tcomp += tc - tb;
    }
    double ttot = MPI_Wtime() - t0;

    double mx[3] = {ttot, tcomp, tcomm}, gmx[3];
    MPI_Reduce(mx, gmx, 3, MPI_DOUBLE, MPI_MAX, 0, grid);

    // ---------------- debugging dump (small N only) ----------------
    if (p.print) {
        for (int k = 0; k < P; ++k) {
            MPI_Barrier(grid);
            if (k == rank) {
                std::printf("rank %d (cx=%d cy=%d) i0=%d nx=%d j0=%d ny=%d, rows top to bottom (g = ghost, as of the last exchange):\n",
                            rank, cx, cy, i0, nx, j0, ny);
                for (int lj = ny + 1; lj >= 0; --lj) {
                    std::printf("  %s", (lj == 0 || lj == ny + 1) ? "g " : "  ");
                    for (int li = 0; li < W; ++li) std::printf("%8.5f ", u[L(li, lj)]);
                    std::printf("\n");
                }
                std::fflush(stdout);
            }
        }
        MPI_Barrier(grid);
    }

    // ---------------- error norms (test V) ----------------
    double einf = 0.0, e2 = 0.0;
    if (p.cas == "V") {
        double decay = std::exp(-2.0 * pi * pi * alpha * steps * dt);
        for (int lj = 1; lj <= ny; ++lj)
            for (int li = 1; li <= nx; ++li) {
                int i = i0 - 1 + li, j = j0 - 1 + lj;
                double e = std::fabs(u[L(li, lj)] - std::sin(pi * i * h) * std::sin(pi * j * h) * decay);
                einf = std::max(einf, e);
                e2 += e * e;
            }
        double g;
        MPI_Reduce(&einf, &g, 1, MPI_DOUBLE, MPI_MAX, 0, grid); einf = g;
        MPI_Reduce(&e2, &g, 1, MPI_DOUBLE, MPI_SUM, 0, grid); e2 = g;
    }

    if (rank == 0) {
        std::printf("decomp=%s P=%d", p.decomp.c_str(), P);
        if (p.decomp == "blocks") std::printf(" Px=%d Py=%d", Px, Py);
        std::printf(" case=%s N=%d r=%.6g steps=%ld T=%.6g t_total=%.6f t_comp=%.6f t_comm=%.6f",
                    p.cas.c_str(), N, rr, steps, steps * dt, gmx[0], gmx[1], gmx[2]);
        if (p.cas == "V") std::printf(" err_inf=%.6e err_2h=%.6e", einf, std::sqrt(h * h * e2));
        std::printf("\n");
        std::fflush(stdout);
    }

    // ---------------- output: rank 0 gathers the full field ----------------
    if (!p.out.empty()) {
        std::vector<double> mine((size_t)nx * ny);
        for (int lj = 0; lj < ny; ++lj)
            for (int li = 0; li < nx; ++li) mine[(size_t)lj * nx + li] = u[L(li + 1, lj + 1)];
        std::vector<int> counts(P), displs(P);
        int cnt = nx * ny;
        MPI_Gather(&cnt, 1, MPI_INT, counts.data(), 1, MPI_INT, 0, grid);
        std::vector<double> all;
        if (rank == 0) {
            for (int k = 0, d = 0; k < P; ++k) { displs[k] = d; d += counts[k]; }
            all.resize((size_t)(N - 1) * (N - 1));
        }
        MPI_Gatherv(mine.data(), cnt, MPI_DOUBLE, all.data(), counts.data(), displs.data(),
                    MPI_DOUBLE, 0, grid);
        if (rank == 0) {
            std::vector<double> field((size_t)n * n);
            for (int j = 0; j < n; ++j)                // boundary values are fixed
                for (int i = 0; i < n; ++i) field[(size_t)j * n + i] = init_value(p.cas, N, i, j);
            for (int k = 0; k < P; ++k) {              // place each rank's block
                int kx = 0, ky = k;
                if (p.decomp == "blocks") { int c[2]; MPI_Cart_coords(cart, k, 2, c); ky = c[0]; kx = c[1]; }
                int ki0, knx, kj0, kny;
                split(N - 1, Px, kx, ki0, knx);
                split(N - 1, Py, ky, kj0, kny);
                if (p.decomp == "serial") { ki0 = 1; knx = N - 1; kj0 = 1; kny = N - 1; }
                const double* b = all.data() + displs[k];
                for (int lj = 0; lj < kny; ++lj)
                    for (int li = 0; li < knx; ++li)
                        field[(size_t)(kj0 + lj) * n + (ki0 + li)] = b[(size_t)lj * knx + li];
            }
            // raw little-endian doubles, (N+1)x(N+1), row j = line y_j, i fastest, no header
            std::ofstream f(p.out, std::ios::binary);
            f.write(reinterpret_cast<const char*>(field.data()), field.size() * sizeof(double));
        }
    }

    MPI_Type_free(&column);
    if (cart != MPI_COMM_NULL) MPI_Comm_free(&cart);
    MPI_Finalize();
    return 0;
}
