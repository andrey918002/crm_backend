import os
import django
import random
from faker import Faker

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm_backend.settings")
django.setup()

from contacts.models import Contact
from store.models import Product
from accounts.models import CustomUser

fake = Faker("ru_RU")


# --- Генерация пользователей ---
def create_users(n=20):
    roles = ["admin", "editor", "user", "guest"]
    for i in range(n):
        username = fake.user_name() + str(random.randint(1, 999))
        email = fake.email()
        role = random.choice(roles)
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password="123456",
            role=role,
        )
        print(f"[+] Пользователь создан: {username} ({role})")


# --- Генерация контактов ---
def create_contacts(n=20):
    for _ in range(n):
        Contact.objects.create(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            phone=fake.phone_number(),
            company=fake.company(),
        )
    print(f"[+] Создано {n} контактов")


# --- Генерация товаров ---
def create_products(n=20):
    for _ in range(n):
        Product.objects.create(
            name=fake.word().capitalize() + " " + fake.word().capitalize(),
            description=fake.text(max_nb_chars=120),
            price=round(random.uniform(10, 500), 2),
            image=f"https://picsum.photos/seed/{random.randint(1,1000)}/400/300",
        )
    print(f"[+] Создано {n} товаров")


if __name__ == "__main__":
    create_users(20)
    create_contacts(20)
    create_products(20)
    print("\n🎉 Все тестовые данные успешно созданы!")
