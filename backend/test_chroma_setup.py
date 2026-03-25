from backend.core.vector_db import create_empty_collection_test


def main() -> None:
    result = create_empty_collection_test()
    print("=== ChromaDB Empty Collection Test ===")
    print(f"ok: {result['ok']}")
    print(f"persist_dir: {result['persist_dir']}")
    print(f"collection_name: {result['collection_name']}")
    print(f"collection_count: {result['collection_count']}")
    print(f"all_collections: {result['all_collections']}")


if __name__ == "__main__":
    main()