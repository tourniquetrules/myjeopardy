import game_logic


def test_initial_buzzers_locked():
    g = game_logic.Game()
    assert g.buzzers_locked is True


def test_clear_buzzers_opens_and_increments_session():
    g = game_logic.Game()
    prev = g.buzz_session
    g.clear_buzzers()
    assert g.buzzers_locked is False
    assert g.buzz_session == prev + 1
