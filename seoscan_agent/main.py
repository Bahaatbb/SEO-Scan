from .agents import SeoOrchestrator

def main():
    print("=== SEOSCAN ===")
    while True:
        query = input("\nYour request: ").strip()
        if query.lower() == "exit":
            break
        print("\n=== SEO Response ===\n")
        print(SeoOrchestrator.chat(query))

if __name__ == "__main__":
    main()