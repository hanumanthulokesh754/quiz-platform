import random


def shuffle_for_attempt(questions: list[dict], attempt_id: str, randomize_questions: bool, randomize_options: bool) -> list[dict]:
    """Returns a new list with question/option order shuffled for this attempt.

    The shuffle is deterministic per (attempt_id, question_id) rather than
    using real randomness on every call — a student refreshing the page or
    resuming an in-progress attempt must see the SAME order each time, or
    their in-progress answers (keyed by question/option id, not position)
    would look like they jumped around. Seeding from attempt_id achieves
    that without persisting a separate "shuffled order" column.
    """
    questions = [dict(q) for q in questions]  # shallow copy, don't mutate caller's list

    if randomize_questions:
        rng = random.Random(f"{attempt_id}:questions")
        rng.shuffle(questions)

    if randomize_options:
        for q in questions:
            options = list(q.get("options", []))
            rng = random.Random(f"{attempt_id}:{q['id']}:options")
            rng.shuffle(options)
            q["options"] = options

    return questions
