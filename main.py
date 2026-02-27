from pathlib import Path

from app.app import build_app


def main() -> None:
    app = build_app(Path(__file__).resolve().parent)
    app.mainloop()


if __name__ == "__main__":
    main()
