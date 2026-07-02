import sys
import os
import time

# Add root directory to path for imports
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.ranker import CandidateRanker


def _str2bool(value: str) -> bool:
    if isinstance(value, bool):
        return value
    lowered = value.lower()
    if lowered in ("yes", "true", "t", "1"):
        return True
    if lowered in ("no", "false", "f", "0"):
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _resolve_path(path_str: str) -> str:
    if not path_str or os.path.isabs(path_str):
        return path_str
    if os.path.exists(path_str):
        return os.path.abspath(path_str)
    root_path = os.path.join(PROJECT_ROOT, path_str)
    if os.path.exists(root_path):
        return os.path.abspath(root_path)
    norm_parts = os.path.normpath(path_str).lstrip(os.sep).split(os.sep)
    if norm_parts[0] in ("data", "output", "artifacts", "models", "config", "scripts", "src"):
        return os.path.abspath(root_path)
    return os.path.abspath(path_str)


def main():
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(PROJECT_ROOT, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            load_dotenv()
    except ImportError:
        pass

    import argparse
    default_top_n = int(os.getenv("TOP_N", "100"))
    default_use_cross_encoder = _str2bool(os.getenv("USE_CROSS_ENCODER", "false"))

    parser = argparse.ArgumentParser(description="Redrob Candidate Ranking System")
    parser.add_argument("--candidates", type=str, default=None, help="Path to input candidates.jsonl")
    parser.add_argument("--out", type=str, default=None, help="Path to output CSV")
    parser.add_argument("--top_n", type=int, default=default_top_n, help="Number of top candidates to output")
    parser.add_argument(
        "--use-cross-encoder",
        type=_str2bool,
        default=default_use_cross_encoder,
        help="Enable Stage 2 cross-encoder rerank (true/false)",
    )
    parser.add_argument(
        "--rerank-pool-size",
        type=int,
        default=int(os.getenv("RERANK_POOL_SIZE", "1500")),
        help="Number of Stage-1 candidates to rerank with cross-encoder (default: 1500)",
    )
    args = parser.parse_args()

    default_cand = os.path.join("data", "candidates.jsonl")
    default_out = os.path.join("output", "submission.csv")

    if (args.candidates is None or args.out is None) and sys.stdin.isatty():
        if args.candidates is None:
            user_cand = input(f"Enter input path (JSONL file or folder) [{default_cand}]: ").strip().strip('"\'')
            args.candidates = user_cand if user_cand else default_cand
        if args.out is None:
            user_out = input(f"Enter output CSV path [{default_out}]: ").strip().strip('"\'')
            args.out = user_out if user_out else default_out

    if args.candidates is None:
        args.candidates = default_cand
    if args.out is None:
        args.out = default_out

    args.candidates = _resolve_path(args.candidates)
    args.out = _resolve_path(args.out)

    if not os.path.exists(args.candidates):
        print(f"Error: Candidate input path not found at '{args.candidates}'.")
        sys.exit(1)

    start_time = time.time()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    ranker = CandidateRanker(
        input_file=args.candidates,
        output_file=args.out,
        top_n=args.top_n,
        use_cross_encoder=args.use_cross_encoder,
        rerank_pool_size=args.rerank_pool_size,
    )
    stage1_seconds, stage2_seconds = ranker.run()

    total_seconds = time.time() - start_time
    print(f"Completed in {total_seconds:.2f} seconds.")
    if args.use_cross_encoder:
        print(f"  Stage 1: {stage1_seconds:.2f}s | Stage 2: {stage2_seconds:.2f}s")


if __name__ == "__main__":
    # Wrap in multiprocessing freeze_support for windows compatibility if packaged
    import multiprocessing
    multiprocessing.freeze_support()
    main()
