from concurrent import futures
import sys
import grpc

from generated import fuzzy_pb2
from generated import fuzzy_pb2_grpc
from damerau import fuzzy_search


class WorkerService(fuzzy_pb2_grpc.SearchWorkerServicer):
    def ProcessChunk(self, request, context):
        local_positions = fuzzy_search(
            request.text,
            request.pattern,
            request.similarity
        )

        global_positions = [
            request.global_offset + pos
            for pos in local_positions
        ]

        return fuzzy_pb2.ChunkResponse(positions=global_positions)


def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))

    fuzzy_pb2_grpc.add_SearchWorkerServicer_to_server(
        WorkerService(),
        server
    )

    server.add_insecure_port(f"0.0.0.0:{port}")
    server.start()

    print(f"Worker pornit pe portul {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 50051
    serve(port)