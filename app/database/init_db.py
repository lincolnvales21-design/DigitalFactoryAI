from app.database.models import create_tables


def init_database():
    create_tables()


if __name__ == "__main__":
    init_database()