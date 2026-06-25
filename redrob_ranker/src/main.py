import sys
import os
import time

# Add root directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.ranker import CandidateRanker

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Redrob Candidate Ranking System")
    parser.add_argument("--candidates", type=str, default=r"data\candidates.jsonl", help="Path to input candidates.jsonl")
    parser.add_argument("--out", type=str, default=r"output\submission.csv", help="Path to output CSV")
    parser.add_argument("--top_n", type=int, default=100, help="Number of top candidates to output")
    args = parser.parse_args()

    start_time = time.time()
    
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    
    ranker = CandidateRanker(input_file=args.candidates, output_file=args.out, top_n=args.top_n)
    ranker.run()
    
    print(f"Completed in {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    # Wrap in multiprocessing freeze_support for windows compatibility if packaged
    import multiprocessing
    multiprocessing.freeze_support()
    main()
