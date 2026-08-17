def calculate_score(questions: list[dict], answers_by_question_id: dict, negative_marks: float = 0) -> dict:
    """Calculates a quiz attempt's score entirely server-side.

    questions: list of question rows, each with its options (each option has
               id + is_correct) and `marks`.
    answers_by_question_id: { question_id: selected_option_id or None }
    negative_marks: marks deducted for each WRONG answer (0 disables negative
               marking; unanswered questions are never penalized). Pass the
               quiz's own `negative_marks` value — never trust a client-supplied
               figure here.

    Returns a dict with correct/incorrect/unanswered counts, obtained marks
    (clamped to zero so a bad run can't go negative), total marks, percentage,
    and per-question correctness — never trusts anything the frontend claims
    about correctness or score.
    """
    total_marks = 0.0
    obtained_marks = 0.0
    correct = 0
    incorrect = 0
    unanswered = 0
    per_question_results = []

    for question in questions:
        q_id = question["id"]
        marks = float(question.get("marks", 1))
        total_marks += marks

        correct_option_id = next(
            (opt["id"] for opt in question.get("options", []) if opt.get("is_correct")),
            None,
        )
        selected_option_id = answers_by_question_id.get(q_id)

        if selected_option_id is None:
            unanswered += 1
            is_correct = None
        elif selected_option_id == correct_option_id:
            correct += 1
            obtained_marks += marks
            is_correct = True
        else:
            incorrect += 1
            obtained_marks -= float(negative_marks)
            is_correct = False

        per_question_results.append(
            {
                "question_id": q_id,
                "selected_option_id": selected_option_id,
                "correct_option_id": correct_option_id,
                "is_correct": is_correct,
            }
        )

    # A quiz's overall score/percentage never goes below zero, even if
    # negative marking outweighs what was answered correctly.
    obtained_marks = max(0.0, obtained_marks)
    percentage = round((obtained_marks / total_marks) * 100, 2) if total_marks > 0 else 0.0

    return {
        "total_marks": total_marks,
        "obtained_marks": obtained_marks,
        "correct_answers": correct,
        "incorrect_answers": incorrect,
        "unanswered": unanswered,
        "percentage": percentage,
        "per_question_results": per_question_results,
    }
