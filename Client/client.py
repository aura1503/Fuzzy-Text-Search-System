import grpc

from generated import fuzzy_pb2
from generated import fuzzy_pb2_grpc


SERVER_ADDRESS = "192.168.1.4:50050"


def main():
    print("Client pornit")
    print("Conectare la server:", SERVER_ADDRESS)

    channel = grpc.insecure_channel(SERVER_ADDRESS)
    stub = fuzzy_pb2_grpc.SearchCoordinatorStub(channel)

    while True:
        print("\nFisiere disponibile pe server:\n")

        file_response = stub.ListFiles(fuzzy_pb2.Empty())

        for index, file in enumerate(file_response.files):
            print(f"{index + 1}. {file}")

        print("\nScrie exit pentru iesire.\n")

        choice = input("Alege numarul fisierului: ")

        if choice.lower() in ["exit", "quit", "stop"]:
            print("Client oprit.")
            break

        choice = int(choice)
        selected_file = file_response.files[choice - 1]

        pattern = input("Introdu cuvantul/fraza de cautat: ")
        similarity = float(input("Introdu gradul de similaritate (0-1): "))

        chunk_input = input("Chunk size [default 1024]: ")
        overlap_input = input("Overlap size [default 50]: ")

        chunk_size = int(chunk_input) if chunk_input.strip() else 1024
        overlap_size = int(overlap_input) if overlap_input.strip() else 50

        request = fuzzy_pb2.SearchRequest(
            file_path=f"data/{selected_file}",
            pattern=pattern,
            similarity=similarity,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )

        print("\nTrimit cererea catre server...")

        response = stub.Search(request)

        print("Pozitii gasite:")
        print(list(response.positions))

        print("\n========== REZULTATE ==========")
        print(f"Fisier: {selected_file}")
        print(f"Pattern cautat: {pattern}")
        print(f"Similaritate: {similarity}")
        print(f"Chunk size: {chunk_size}")
        print(f"Overlap size: {overlap_size}")
        print(f"Numar workeri: {response.numar_workeri}")
        print("--------------------------------")
        print(f"Timp nedistribuit: {response.timp_nedistribuit:.6f} secunde")
        print(f"Timp distribuit:   {response.timp_distribuit:.6f} secunde")
        print(f"Speedup:           {response.speedup:.2f}x")
        print("--------------------------------")
        print(f"Throughput nedistribuit: {response.throughput_nedistribuit:.2f} caractere/secunda")
        print(f"Throughput distribuit:   {response.throughput_distribuit:.2f} caractere/secunda")
        print("--------------------------------")
        print(f"Aparitii nedistribuit: {response.aparitii_nedistribuit}")
        print(f"Aparitii distribuit:   {response.aparitii_distribuit}")
        print("================================\n")


if __name__ == "__main__":
    main()