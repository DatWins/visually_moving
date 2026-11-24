#!/usr/bin/env python3 -I
"""
filter_puzzles.py — convert Lichess puzzle CSV into text-only visualization
exercises for the Visually Moving site.

Generates three exercise types:
  1. how-would-you-play   — position in notation + "find the move"
  2. determine-positions   — position + continuation → where do pieces end up?
  3. play-out-the-game     — full game moves from move 1 → find the winning move

Usage
-----
1. Download the puzzle CSV from https://database.lichess.org/#puzzles
   (file is called lichess_db_puzzle.csv.zst).
   Decompress it:   zstd -d lichess_db_puzzle.csv.zst
2. Run:
       python filter_puzzles.py --csv lichess_db_puzzle.csv
   This writes JSON files into static/data/.
   Add --max N to cap the number of puzzles per type (default 200).

Requirements: python-chess   (pip install chess)
"""

import argparse, csv, json, os, sys, time, urllib.request
import chess

# ── FEN to text notation ──────────────────────────────────────────────

PIECE_ORDER = [chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
PIECE_NAMES = {
    chess.KING: "K", chess.QUEEN: "Q", chess.ROOK: "R",
    chess.BISHOP: "B", chess.KNIGHT: "N"
}

def fen_to_text(fen):
    """Convert a FEN string to notation like:
       White: Kg1, Qd1, Rd1, Ps f2, g2, h2
       Returns (white_str, black_str).
    """
    board = chess.Board(fen)
    white_parts = []
    black_parts = []
    white_pawns = []
    black_pawns = []

    for pt in PIECE_ORDER:
        for sq in sorted(board.pieces(pt, chess.WHITE)):
            white_parts.append(PIECE_NAMES[pt] + chess.square_name(sq))
        for sq in sorted(board.pieces(pt, chess.BLACK)):
            black_parts.append(PIECE_NAMES[pt] + chess.square_name(sq))

    for sq in sorted(board.pieces(chess.PAWN, chess.WHITE)):
        white_pawns.append(chess.square_name(sq))
    for sq in sorted(board.pieces(chess.PAWN, chess.BLACK)):
        black_pawns.append(chess.square_name(sq))

    white_str = ", ".join(white_parts)
    if white_pawns:
        if len(white_pawns) == 1:
            white_str += ", P" + white_pawns[0]
        else:
            white_str += ", Ps " + ", ".join(white_pawns)

    black_str = ", ".join(black_parts)
    if black_pawns:
        if len(black_pawns) == 1:
            black_str += ", P" + black_pawns[0]
        else:
            black_str += ", Ps " + ", ".join(black_pawns)

    return white_str, black_str


def uci_to_san(board, uci_str):
    """Push a UCI move on a board (mutates it) and return its SAN."""
    move = chess.Move.from_uci(uci_str)
    san = board.san(move)
    board.push(move)
    return san


def to_move_str(fen):
    """Return 'White' or 'Black' based on whose turn it is in the FEN."""
    return "Black" if fen.split()[1] == "b" else "White"


def move_number(fen):
    """Return the full-move number from a FEN."""
    try:
        return int(fen.split()[5])
    except (IndexError, ValueError):
        return 1


def format_san_sequence(sans, start_fen):
    """Format a list of SANs with move numbers, e.g. '1.e4 e5 2.Nf3'."""
    color = start_fen.split()[1]  # 'w' or 'b'
    move_no = move_number(start_fen)
    parts = []
    for i, san in enumerate(sans):
        is_white = (color == "w" and i % 2 == 0) or (color == "b" and i % 2 == 1)
        if is_white:
            parts.append(f"{move_no}.{san}")
        else:
            if i == 0 and color == "b":
                parts.append(f"{move_no}...{san}")
            else:
                parts.append(san)
            move_no += 1
    return " ".join(parts)


# ── Lichess game fetcher (for play-out-the-game) ─────────────────────

def fetch_game_moves(game_url):
    """Fetch a Lichess game's SAN moves via the export API.
    Returns list of SAN strings, or [] on error."""
    import re
    try:
        parts = game_url.rstrip("/").split("/")
        game_id = parts[-1].split("#")[0]
        if game_id in ("white", "black"):
            game_id = parts[-2].split("#")[0]
        api_url = (f"https://lichess.org/game/export/{game_id}"
                   "?moves=true&tags=false&clocks=false&evals=false"
                   "&opening=false&literate=false")
        req = urllib.request.Request(api_url,
                headers={"Accept": "application/x-chess-pgn"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            pgn_text = resp.read().decode()
        pgn_text = re.sub(r'\[.*?\]', '', pgn_text)
        pgn_text = re.sub(r'\d+\.+', '', pgn_text)
        pgn_text = re.sub(r'\{[^}]*\}', '', pgn_text)
        tokens = pgn_text.split()
        result_tokens = {'1-0', '0-1', '1/2-1/2', '*'}
        return [t for t in tokens if t not in result_tokens]
    except Exception:
        return []


def find_game_context(game_url, start_fen, context_plies=20):
    """Fetch a game and return the first N moves leading up to the puzzle.
    Returns (san_list_from_move_1, puzzle_to_move_str) or ([], "")."""
    san_moves = fetch_game_moves(game_url)
    if not san_moves:
        return [], ""

    board = chess.Board()
    target_key = " ".join(start_fen.split()[:4])
    match_ply = None

    for i, san in enumerate(san_moves):
        cur_key = " ".join(board.fen().split()[:4])
        if cur_key == target_key:
            match_ply = i
            break
        try:
            board.push_san(san)
        except Exception:
            break

    if match_ply is None:
        return [], ""

    # We want the moves from the start of the game up to the puzzle position.
    # For "play out the game" exercises, we show all moves from move 1.
    # Cap at context_plies to keep exercises manageable.
    start_ply = max(0, match_ply - context_plies)
    # Always start from move 1 for blindfold exercises
    start_ply = 0

    board2 = chess.Board()
    context_sans = []
    for san in san_moves[start_ply:match_ply]:
        try:
            board2.push_san(san)
            context_sans.append(san)
        except Exception:
            break

    return context_sans, to_move_str(board2.fen())


# ── main processing ──────────────────────────────────────────────────

def process_row(row):
    """Parse one CSV row. Returns (start_fen, puzzle_fen, lead_in_san,
    solution_sans, themes, game_url) or None."""
    try:
        puzzle_id = row[0].strip()
        start_fen = row[1].strip()
        moves_uci = row[2].strip().split()
        themes    = row[7].strip().split() if len(row) > 7 else []
        game_url  = row[8].strip() if len(row) > 8 else ""
    except IndexError:
        return None

    if len(moves_uci) < 2:
        return None

    board = chess.Board(start_fen)
    all_sans = []
    puzzle_fen = None
    try:
        for i, uci in enumerate(moves_uci):
            all_sans.append(uci_to_san(board, uci))
            if i == 0:
                puzzle_fen = board.fen()
    except Exception:
        return None

    if puzzle_fen is None:
        return None

    return {
        "puzzle_id": puzzle_id,
        "start_fen": start_fen,
        "puzzle_fen": puzzle_fen,
        "lead_in": all_sans[0],
        "solution": all_sans[1:],
        "themes": themes,
        "game_url": game_url,
        "final_fen": board.fen(),
    }


def make_how_would_you_play(parsed):
    """Build a 'how would you play' exercise from a parsed puzzle."""
    white_str, black_str = fen_to_text(parsed["puzzle_fen"])
    to_move = to_move_str(parsed["puzzle_fen"])

    # Format solution with move numbers
    sol_sans = format_san_sequence(parsed["solution"], parsed["puzzle_fen"])

    return {
        "id": parsed["puzzle_id"],
        "white": white_str,
        "black": black_str,
        "toMove": to_move,
        "solution": [sol_sans],
        "site": "https://lichess.org/training/" + parsed["puzzle_id"],
    }


def make_determine_positions(parsed):
    """Build a 'determine positions' exercise.
    Shows starting position + continuation, asks for final position."""
    white_str, black_str = fen_to_text(parsed["puzzle_fen"])

    # Continuation = the solution moves
    cont = format_san_sequence(parsed["solution"], parsed["puzzle_fen"])

    # Final position after all solution moves
    sol_white, sol_black = fen_to_text(parsed["final_fen"])

    return {
        "id": parsed["puzzle_id"],
        "white": white_str,
        "black": black_str,
        "continuation": cont,
        "solutionWhite": sol_white,
        "solutionBlack": sol_black,
        "site": "https://lichess.org/training/" + parsed["puzzle_id"],
    }


def make_play_out_the_game(parsed, game_sans):
    """Build a 'play out the game' exercise from fetched game moves."""
    # Format game moves from move 1
    board = chess.Board()
    parts = []
    for i, san in enumerate(game_sans):
        if i % 2 == 0:
            parts.append(f"{i//2 + 1}.{san}")
        else:
            parts.append(san)
    moves_text = " ".join(parts)

    to_move = to_move_str(parsed["puzzle_fen"])

    # Solution is the first move of the puzzle solution
    sol = format_san_sequence(parsed["solution"][:1], parsed["puzzle_fen"])
    # Full line if multi-move
    full = format_san_sequence(parsed["solution"], parsed["puzzle_fen"]) if len(parsed["solution"]) > 1 else ""

    return {
        "id": parsed["puzzle_id"],
        "moves": moves_text,
        "toMove": to_move,
        "solution": [sol],
        "fullLine": full,
        "site": "https://lichess.org/training/" + parsed["puzzle_id"],
    }


def main():
    ap = argparse.ArgumentParser(
        description="Filter Lichess puzzles CSV into text-only "
                    "visualization exercises for Visually Moving.")
    ap.add_argument("--csv", required=True,
                    help="Path to lichess_db_puzzle.csv")
    ap.add_argument("--out", default="static/data",
                    help="Output directory (default: static/data)")
    ap.add_argument("--max", type=int, default=200,
                    help="Max puzzles per exercise type (default: 200)")
    ap.add_argument("--fetch-games", action="store_true",
                    help="Fetch game context from Lichess API for "
                         "'play out the game' exercises (slow, ~1 req/sec)")
    ap.add_argument("--min-rating", type=int, default=1200,
                    help="Minimum puzzle rating (default: 1200)")
    ap.add_argument("--max-rating", type=int, default=2200,
                    help="Maximum puzzle rating (default: 2200)")
    ap.add_argument("--max-pieces", type=int, default=12,
                    help="Max pieces on board for how-would-you-play "
                         "(simpler positions are easier to visualize, "
                         "default: 12)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    hwp_list = []   # how-would-you-play
    dp_list  = []   # determine-positions
    potg_list = []  # play-out-the-game

    hwp_full = dp_full = potg_full = False

    print(f"Reading {args.csv} ...")
    print(f"  Rating range: {args.min_rating}–{args.max_rating}")
    print(f"  Max pieces for 'how would you play': {args.max_pieces}")
    print(f"  Max per type: {args.max}")

    with open(args.csv, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for lineno, row in enumerate(reader, 1):
            if lineno % 100_000 == 0:
                print(f"  line {lineno:,} — "
                      f"hwp:{len(hwp_list)} dp:{len(dp_list)} "
                      f"potg:{len(potg_list)}")

            if hwp_full and dp_full and potg_full:
                break

            # Rating filter
            try:
                rating = int(row[3].strip())
            except (IndexError, ValueError):
                continue
            if rating < args.min_rating or rating > args.max_rating:
                continue

            parsed = process_row(row)
            if parsed is None:
                continue

            # Count pieces on the puzzle board
            board = chess.Board(parsed["puzzle_fen"])
            piece_count = len(board.piece_map())

            # ── how-would-you-play: simpler positions, 1-move solutions ──
            if (not hwp_full and
                piece_count <= args.max_pieces and
                len(parsed["solution"]) <= 3):
                hwp_list.append(make_how_would_you_play(parsed))
                if len(hwp_list) >= args.max:
                    hwp_full = True
                    print(f"  'how-would-you-play' full at line {lineno:,}")

            # ── determine-positions: 2-4 move solutions ──
            if (not dp_full and
                piece_count <= 16 and
                2 <= len(parsed["solution"]) <= 6):
                dp_list.append(make_determine_positions(parsed))
                if len(dp_list) >= args.max:
                    dp_full = True
                    print(f"  'determine-positions' full at line {lineno:,}")

            # ── play-out-the-game: needs game fetch ──
            if (not potg_full and
                args.fetch_games and
                parsed["game_url"] and
                piece_count >= 20):  # positions with lots of pieces = early game
                n = len(potg_list) + 1
                print(f"  [{n}/{args.max}] fetching {parsed['game_url']} ...",
                      end=" ", flush=True)
                game_sans, _ = find_game_context(
                    parsed["game_url"], parsed["start_fen"])
                if game_sans and len(game_sans) >= 8:
                    potg_list.append(
                        make_play_out_the_game(parsed, game_sans))
                    print(f"ok ({len(game_sans)} plies)")
                else:
                    print("skipped")
                time.sleep(1)  # be polite to Lichess API
                if len(potg_list) >= args.max:
                    potg_full = True

    # Write JSON files
    for name, data in [
        ("how-would-you-play", hwp_list),
        ("determine-positions", dp_list),
        ("play-out-the-game", potg_list),
    ]:
        path = os.path.join(args.out, name + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        print(f"  wrote {len(data):>4} exercises -> {path}")

    print("Done.")
    if not args.fetch_games:
        print("\nNote: 'play-out-the-game' exercises require --fetch-games")
        print("to download game context from Lichess (slow, ~1 req/sec).")
        print("Without it, only the sample data is used.")


if __name__ == "__main__":
    main()
