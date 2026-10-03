from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Geliştirme aşamasında hızlı ilerlemek için şimdilik yerel SQLite kullanıyoruz.
# PostgreSQL'e geçeceğimiz zaman sadece bu adresi değiştireceğiz!
SQLALCHEMY_DATABASE_URL = "sqlite:///./omnilog.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Bütün modellerimizin miras alacağı ana sınıf:
Base = declarative_base()


# API isteklerinde veritabanı bağlantısını açıp kapatacak yardımcı fonksiyon
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()