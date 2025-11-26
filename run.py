# run.py
# Core game loop for Quizbowl Challenge

from packet_loader import load_packets
from stats_manager import StatsManager

def play_game(format_type):
    stats = StatsManager()
    stats.add_player("Player1")  # Example single player setup

    packets = load_packets(format_type)
    if not packets:
        print(f"No {format_type} packets loaded!")
        return

    # Iterate through packets/questions
    for packet in packets:
        for q in packet["questions"]:
            if q["type"] == "tossup":
                print("\nTOSSUP:")
                print(f"Hard: {q['difficulty']['hard']}")
                print(f"Medium: {q['difficulty']['medium']}")
                print(f"Easy: {q['difficulty']['easy']}")

                # Simulate buzz + answer
                stats.buzz_in("Player1")
                given_answer = input("Your answer: ")
                correct_answer = q["answer"]

                if stats.check_answer("Player1", given_answer, correct_answer):
                    print("✅ Correct! +1 point")
                else:
                    print(f"❌ Incorrect. Correct answer was: {correct_answer}")

            elif q["type"] == "bonus":
                print("\nBONUS:")
                for part in q["parts"]:
                    print(f"Q: {part['text']}")
                    given_answer = input("Your answer: ")
                    correct_answer = part["answer"]

                    if stats.check_answer("Player1", given_answer, correct_answer):
                        print("✅ Correct! +1 point")
                    else:
                        print(f"❌ Incorrect. Correct answer was: {correct_answer}")

            elif q["type"] == "sixty_second":
                print("\n60-SECOND ROUND:")
                print(f"Q: {q['text']}")
                given_answer = input("Your answer: ")
                correct_answer = q["answer"]

                if stats.check_answer("Player1", given_answer, correct_answer):
                    print("✅ Correct! +1 point")
                else:
                    print(f"❌ Incorrect. Correct answer was: {correct_answer}")

    # Final scores
    print("\nFinal Scores:")
    for name, score in stats.get_all_scores().items():
        print(f"{name}: {score}")

if __name__ == "__main__":
    print("Choose format: NAQT / OSSAA / Froshmore / Trivia")
    choice = input("Format: ").strip()
    play_game(choice)
