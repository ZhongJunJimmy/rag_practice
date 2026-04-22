try:
    from _common import setup_path
except ImportError:
    from scripts._common import setup_path

setup_path()

from datetime import datetime
import time
from services.web_search import run_agent
from services.query import rewrite_query

def main() -> None:
    print("Type 'exit' to quit.\n")

    while True:
        user_question = input("You: ").strip()
        # rewrite = rewrite_query(user_question)
        print(f"User question: {user_question}")
        if not user_question:
            continue
        if user_question.lower() in {"exit", "quit"}:
            break

        now = datetime.now()
        user_question = user_question+f" (asked at {now.strftime('%Y-%m-%d %H:%M:%S')})"
        start = time.time()
        try:
            answer = run_agent(user_question)
            print(f"\nAssistant:\n{answer}\n")
        except Exception as e:
            print(f"\nError: {e}\n")
        finally:
            print(f"[elapsed: {time.time() - start:.2f}s]\n")


if __name__ == "__main__":
    main()