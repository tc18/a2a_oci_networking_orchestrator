
from agents.orchestrator import Orchestrator

def main():
    print("OCI A2A Assistant (type 'exit' to quit)\n")
    orchestrator = Orchestrator()

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not question or question.lower() == "exit":
            break

        print()
        answer = orchestrator.run(question)
        print(f"\nAssistant: {answer}\n")
        print("-" * 60)

if __name__ == "__main__":
    main()