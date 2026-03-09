from bpui.core.content_validation import detect_user_authorship_issues


def test_instruction_not_to_narrate_user_does_not_trigger_false_positive():
    text = "Never narrate {{user}}'s thoughts, actions, or consent."

    assert detect_user_authorship_issues(text) == []


def test_actual_user_internal_state_still_triggers_issue():
    text = "{{user}}'s thoughts spiral as the room closes in around them."

    assert detect_user_authorship_issues(text) == ["Narrates {{user}} internal state"]


def test_actual_user_action_still_triggers_issue():
    text = "{{user}} smiles and steps closer to the doorway."

    assert detect_user_authorship_issues(text) == ["Narrates {{user}} action/thought/consent"]