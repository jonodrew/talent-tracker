from modules.seed import commit_data, clear_old_data
from app import create_app


def main():
    app = create_app()
    with app.app_context():
        clear_old_data()
        commit_data()


if __name__ == '__main__':
    main()
