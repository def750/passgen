import argparse
import secrets
import shutil
import subprocess
import sys
import unicodedata

ASCII_CHARACTERS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    "[]<>!@#$%^&*()_+-=~`|;:,.?/{}"
)

SIMPLE_CHARACTERS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*_-+="
)

UNICODE_CHARACTERS = "".join(
    chr(codepoint)
    for codepoint in range(0x80, 0x10000)
    if unicodedata.category(chr(codepoint)).startswith("L")
)

RNG = secrets.SystemRandom()


def percentage(value: str) -> float:
    try:
        percent = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Percentage must be a number") from exc

    if not 0 <= percent <= 100:
        raise argparse.ArgumentTypeError("Percentage must be between 0 and 100")

    return percent


def generate_password(
    length: int = 32,
    fuck_percent: float = 25,
    space_percent: float = 0,
    simple: bool = False,
) -> str:
    if length < 3:
        raise ValueError("Password length must be at least 3")

    spaces = max(1, round(length * space_percent / 100))
    unicode_count = 0 if simple else round(length * fuck_percent / 100)

    if spaces > length - 2:
        raise ValueError("Too many spaces: first and last characters cannot be spaces")

    if unicode_count + spaces > length:
        raise ValueError("Unicode and space percentages exceed password length")

    ascii_pool = SIMPLE_CHARACTERS if simple else ASCII_CHARACTERS

    characters = [secrets.choice(UNICODE_CHARACTERS) for _ in range(unicode_count)] + [
        secrets.choice(ascii_pool) for _ in range(length - unicode_count - spaces)
    ]

    RNG.shuffle(characters)

    space_positions = set(RNG.sample(range(1, length - 1), spaces))

    iterator = iter(characters)

    return "".join(
        " " if i in space_positions else next(iterator) for i in range(length)
    )


def copy_to_clipboard(password: str) -> None:
    commands = (
        ("wl-copy",),
        ("xclip", "-selection", "clipboard"),
        ("xsel", "--clipboard", "--input"),
        ("pbcopy",),
        ("clip",),
    )

    for command in commands:
        if not shutil.which(command[0]):
            continue

        try:
            subprocess.run(
                command,
                input=password.encode("utf-8"),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
        except (OSError, subprocess.CalledProcessError):
            continue

    raise RuntimeError("Clipboard unavailable (install wl-clipboard on Wayland)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cryptographically secure Unicode password generator"
    )

    parser.add_argument(
        "-l",
        "--length",
        type=int,
        default=32,
        metavar="N",
        help="Password length (default: 32)",
    )

    parser.add_argument(
        "-f",
        "--fuck",
        type=percentage,
        default=25,
        metavar="PERCENT",
        help="Percentage of Unicode characters (default: 25)",
    )

    parser.add_argument(
        "-s",
        "--spaces",
        type=percentage,
        default=0,
        metavar="PERCENT",
        help="Percentage of spaces (default: one space)",
    )

    parser.add_argument(
        "--simple",
        action="store_true",
        help="ASCII-only mode for restrictive websites",
    )

    parser.add_argument(
        "-r",
        "--repeat",
        action="store_true",
        help="Interactive regeneration loop",
    )

    parser.add_argument(
        "-nc",
        "--no-copy",
        action="store_true",
        help="Disable clipboard copying",
    )

    parser.add_argument(
        "-ecdsa",
        action="store_true",
        help="Generate an ECDSA certificate",
    )

    args = parser.parse_args()

    try:
        while True:
            password = (
                "4"
                if args.ecdsa
                else generate_password(
                    length=args.length,
                    fuck_percent=args.fuck,
                    space_percent=args.spaces,
                    simple=args.simple,
                )
            )

            print(password)

            if not args.no_copy:
                try:
                    copy_to_clipboard(password)
                except RuntimeError as exc:
                    print(f"Warning: {exc}", file=sys.stderr)

            if not args.repeat:
                break

            answer = input("Regenerate password? (Y/n): ")
            if answer.strip().lower() not in ("y", ""):
                break

    except ValueError as exc:
        parser.error(str(exc))
    except (EOFError, KeyboardInterrupt):
        print(file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
