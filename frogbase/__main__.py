"""Command-line interface."""
import argparse


def demo(args) -> None:
    from frogbase import FrogBase

    fb = FrogBase(datadir=args.datadir, library=args.library, verbose=args.verbose, dev=args.dev, persist=args.persist)
    fb.demo()
    fb.media.show()


def main() -> None:
    """FrogBase runner."""
    parser = argparse.ArgumentParser(description="FrogBase CLI")
    # Add a positional/required argument
    parser.add_argument("command", type=str, help="Command to run.")
    parser.add_argument("--datadir", type=str, default="./local/data", help="Path to the output directory.")
    parser.add_argument("--library", type=str, default="frogverse", help="Name of the library to use.")
    parser.add_argument("--persist", action="store_true", help="Enable persistent storage.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    parser.add_argument("--dev", action="store_true", help="Enable development mode.")
    args = parser.parse_args()

    # Invoke the subcommand
    if args.command == "demo":
        demo(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()  # pragma: no cover
