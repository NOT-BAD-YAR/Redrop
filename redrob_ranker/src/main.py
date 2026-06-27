import sys
import os
import time

# Add root directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

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


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Redrob Candidate Ranking System")
    parser.add_argument("--candidates", type=str, default=r"data\candidates.jsonl", help="Path to input candidates.jsonl")
    parser.add_argument("--out", type=str, default=r"output\submission.csv", help="Path to output CSV")
    parser.add_argument("--top_n", type=int, default=100, help="Number of top candidates to output")
    parser.add_argument(
        "--use-cross-encoder",
        type=_str2bool,
        default=False,
        help="Enable Stage 2 cross-encoder rerank on top 500 (true/false)",
    )
    args = parser.parse_args()

    if "--candidates" not in sys.argv:
        user_input = input(f"Enter path to candidates file or directory [default: {args.candidates}]: ").strip().strip('"\'')
        if user_input:
            args.candidates = user_input

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
