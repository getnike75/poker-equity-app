import streamlit as st
import eval7

st.set_page_config(page_title="Poker Equity & EV Calculator", page_icon="♠️")


def parse_cards(card_str: str):
    """Convert a string like 'As Kd' or 'AsKd' into a list of eval7.Card objects."""
    card_str = card_str.strip()
    if not card_str:
        return []
    tokens = card_str.replace(',', ' ').split()
    # Handle compact form: "AsKdQh" -> ["As", "Kd", "Qh"]
    if len(tokens) == 1 and len(card_str) % 2 == 0 and len(card_str) > 2:
        tokens = [card_str[i:i + 2] for i in range(0, len(card_str), 2)]
    try:
        return [eval7.Card(tok) for tok in tokens if tok]
    except Exception as e:
        raise ValueError(f"Bad card string '{card_str}': {e}")


def equity_vs_players(hand, board, num_opponents, iters):
    """Monte‑Carlo estimate of hero equity versus num_opponents opponents."""
    wins = ties = 0
    for _ in range(iters):
        deck = eval7.Deck()
        for c in hand + board:
            deck.cards.remove(c)
        deck.shuffle()

        full_board = board + deck.deal(5 - len(board))
        opp_hands = [deck.deal(2) for _ in range(num_opponents)]

        hero_val = eval7.evaluate(hand + full_board)
        opp_vals = [eval7.evaluate(oh + full_board) for oh in opp_hands]
        max_opp = max(opp_vals)
        if hero_val > max_opp:
            wins += 1
        elif hero_val == max_opp:
            ties += 1
    return (wins + ties / 2) / iters


# UI
st.title("♠️ Hold'em Equity & EV Trainer")

with st.form("input_form"):
    col1, col2 = st.columns(2)
    with col1:
        hand_str = st.text_input("Your two hole cards", placeholder="As Kd")
        board_str = st.text_input("Board cards (0–5)", placeholder="Qh Jh Th")
        players = st.slider("Number of opponents", min_value=1, max_value=8, value=1)
    with col2:
        pot = st.number_input("Pot size before facing bet ($)", min_value=0.0, step=0.5, value=0.0, format="%.2f")
        bet = st.number_input("Call amount ($)", min_value=0.0, step=0.5, value=0.0, format="%.2f")
        iters = st.number_input("Monte‑Carlo iterations", min_value=1000, max_value=1_000_000, step=1000, value=30000)
    submitted = st.form_submit_button("Run Calculation")

if submitted:
    try:
        hand = parse_cards(hand_str)
        board = parse_cards(board_str)
        if len(hand) != 2:
            st.error("Enter exactly two hole cards.")
            st.stop()
        if len(board) not in {0, 3, 4, 5}:
            st.error("Board must have 0, 3, 4, or 5 cards.")
            st.stop()

        equity = equity_vs_players(hand, board, players, int(iters))
        st.markdown(f"**Win equity:** {equity*100:.2f}%")

        if bet > 0:
            pot_odds = bet / (pot + bet)
            st.markdown(f"**Pot odds:** {pot_odds*100:.2f}%")
            if equity > pot_odds:
                st.success("✅ CALL (+EV)")
            else:
                st.error("❌ FOLD (‑EV)")
        else:
            st.info("No bet to call – equity shown for reference.")
    except Exception as e:
        st.error(f"Input error: {e}")
