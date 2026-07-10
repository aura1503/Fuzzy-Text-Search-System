from concurrent import futures
import os
import sys
import time
import grpc

from generated import fuzzy_pb2
from generated import fuzzy_pb2_grpc
from damerau import fuzzy_search


DATA_FOLDER = "data"


class CoordinatorService(fuzzy_pb2_grpc.SearchCoordinatorServicer):
    def __init__(self, workers):
        self.worker_stubs = []

        print("Workeri activi:")

        for worker in workers:
            print("-", worker)
            channel = grpc.insecure_channel(worker)
            stub = fuzzy_pb2_grpc.SearchWorkerStub(channel)
            self.worker_stubs.append(stub)

    def ListFiles(self, request, context):
        peer = context.peer()
        print(f"\nClient conectat: {peer}")

        files = []

        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)

        for file in os.listdir(DATA_FOLDER):
            if file.endswith(".txt"):
                files.append(file)

        return fuzzy_pb2.FileList(files=files)

    def run_nedistribuit(self, file_path, pattern, similarity):
        start_time = time.time()

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        positions = fuzzy_search(text, pattern, similarity)

        execution_time = time.time() - start_time
        throughput = len(text) / execution_time if execution_time > 0 else 0

        return sorted(set(positions)), execution_time, throughput, len(text)

    def run_distribuit(self, file_path, pattern, similarity, chunk_size, overlap_size):
        start_time = time.time()

        if not self.worker_stubs:
            raise Exception("Nu exista workeri disponibili.")

        tasks = []

        executor = futures.ThreadPoolExecutor(
            max_workers=len(self.worker_stubs)
        )

        offset = 0
        worker_index = 0
        previous_overlap = ""
        total_chars = 0

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            while True:
                chunk = f.read(chunk_size)

                if not chunk:
                    break

                total_chars += len(chunk)

                full_chunk = previous_overlap + chunk
                global_offset = max(0, offset - len(previous_overlap))

                stub = self.worker_stubs[worker_index]

                chunk_request = fuzzy_pb2.ChunkRequest(
                    text=full_chunk,
                    pattern=pattern,
                    similarity=similarity,
                    global_offset=global_offset
                )

                task = executor.submit(stub.ProcessChunk, chunk_request)
                tasks.append(task)

                previous_overlap = chunk[-overlap_size:] if overlap_size > 0 else ""
                offset += len(chunk)

                worker_index = (worker_index + 1) % len(self.worker_stubs)

        positions = []

        for task in tasks:
            response = task.result()
            positions.extend(response.positions)

        positions = sorted(set(positions))

        execution_time = time.time() - start_time
        throughput = total_chars / execution_time if execution_time > 0 else 0

        return positions, execution_time, throughput, total_chars

    def Search(self, request, context):
        peer = context.peer()
        print(f"\nClient conectat: {peer}")
        print("Proces inceput")

        try:
            positions_nedistribuit, timp_nedistribuit, throughput_nedistribuit, total_chars = (
                self.run_nedistribuit(
                    request.file_path,
                    request.pattern,
                    request.similarity
                )
            )

            positions_distribuit, timp_distribuit, throughput_distribuit, _ = (
                self.run_distribuit(
                    request.file_path,
                    request.pattern,
                    request.similarity,
                    request.chunk_size,
                    request.overlap_size
                )
            )

            speedup = timp_nedistribuit / timp_distribuit if timp_distribuit > 0 else 0

            print("Proces terminat")

            return fuzzy_pb2.SearchResponse(
                positions=positions_distribuit,
                timp_nedistribuit=timp_nedistribuit,
                timp_distribuit=timp_distribuit,
                throughput_nedistribuit=throughput_nedistribuit,
                throughput_distribuit=throughput_distribuit,
                speedup=speedup,
                aparitii_nedistribuit=len(positions_nedistribuit),
                aparitii_distribuit=len(positions_distribuit),
                total_chars=total_chars,
                numar_workeri=len(self.worker_stubs)
            )

        except Exception as e:
            print("Eroare:", str(e))
            context.abort(grpc.StatusCode.INTERNAL, str(e))


def serve(workers):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))

    fuzzy_pb2_grpc.add_SearchCoordinatorServicer_to_server(
        CoordinatorService(workers),
        server
    )

    server.add_insecure_port("0.0.0.0:50050")
    server.start()

    print("Server pornit pe portul 50050")
    server.wait_for_termination()


if __name__ == "__main__":
    workers = sys.argv[1:]

    if not workers:
        workers = ["localhost:50051"]

    serve(workers)