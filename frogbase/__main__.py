"""Command-line interface."""
import argparse

from frogbase import FrogBase


def main(args) -> None:
    """FrogBase runner."""
    fb = FrogBase(datadir=args.datadir, library=args.library, verbose=args.verbose, dev=args.dev, persist=args.persist)
    fb.demo()
    fb.media.show()


if __name__ == "__main__":
    # Add command-line arguments for datadir, verbose, & dev
    parser = argparse.ArgumentParser(description="FrogBase CLI")
    parser.add_argument("--datadir", type=str, default="./local/data", help="Path to the output directory.")
    parser.add_argument("--library", type=str, default="main", help="Name of the library to use.")
    parser.add_argument("--persist", action="store_true", help="Enable persistent storage.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    parser.add_argument("--dev", action="store_true", help="Enable development mode.")
    args = parser.parse_args()

    main(args)  # pragma: no cover
