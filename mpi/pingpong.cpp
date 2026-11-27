// Ping-pong between rank 0 and rank 1, m = 8 B .. 16 MB (powers of two).
// Prints CSV: bytes,reps,one_way_s,bandwidth_MBps
#include <mpi.h>
#include <cstdio>
#include <vector>

static void exchange(int rank, char* buf, long m) {
    if (rank == 0) {
        MPI_Send(buf, (int)m, MPI_CHAR, 1, 0, MPI_COMM_WORLD);
        MPI_Recv(buf, (int)m, MPI_CHAR, 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    } else {
        MPI_Recv(buf, (int)m, MPI_CHAR, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        MPI_Send(buf, (int)m, MPI_CHAR, 0, 0, MPI_COMM_WORLD);
    }
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank, size, len;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    if (size != 2) {
        if (rank == 0) std::fprintf(stderr, "Run with exactly 2 processes.\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    char me[MPI_MAX_PROCESSOR_NAME] = {0}, other[MPI_MAX_PROCESSOR_NAME] = {0};
    MPI_Get_processor_name(me, &len);
    if (rank == 1) MPI_Send(me, MPI_MAX_PROCESSOR_NAME, MPI_CHAR, 0, 9, MPI_COMM_WORLD);
    else {
        MPI_Recv(other, MPI_MAX_PROCESSOR_NAME, MPI_CHAR, 1, 9, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        std::printf("# %s <-> %s\nbytes,reps,one_way_s,bandwidth_MBps\n", me, other);
    }

    const long maxBytes = 16L * 1024 * 1024;
    std::vector<char> buf(maxBytes, 1);

    for (long m = 8; m <= maxBytes; m *= 2) {
        int reps = m <= 65536 ? 200 : (m <= 1048576 ? 50 : 10);
        for (int w = 0; w < 3; ++w) exchange(rank, buf.data(), m);   // warm-up
        MPI_Barrier(MPI_COMM_WORLD);
        double t0 = MPI_Wtime();
        for (int r = 0; r < reps; ++r) exchange(rank, buf.data(), m);
        double oneWay = (MPI_Wtime() - t0) / reps / 2.0;
        if (rank == 0) {
            std::printf("%ld,%d,%.9e,%.3f\n", m, reps, oneWay, m / oneWay / 1e6);
            std::fflush(stdout);
        }
    }
    MPI_Finalize();
    return 0;
}
