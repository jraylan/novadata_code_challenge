from faker import Faker

from django.contrib.auth.models import User

from apps.forum.models import Post, Comment


fake = Faker('pt-BR')

users = [*User.objects.all()]

def create_comment(post, count=1):
    
    for _ in range(count):
        Comment.objects.create(
            content=fake.paragraph(
                nb_sentences=fake.random.randint(3, 10)),
            post=post,
            author=fake.random.choice(users))


def create_posts(count=1):
    for _ in range(count):
        post = Post.objects.create(
            title=fake.paragraph(nb_sentences=1),
            content=fake.paragraph(
                        nb_sentences=fake.random.randint(7, 15)),
            author=fake.random.choice(users))

        create_comment(post, fake.random.randint(3, 10))


def create_users(count=1):
    for _ in range(count):
        profile = fake.simple_profile()
        print(profile)
        user = User.objects.create(
            username=profile['username'],
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=profile['mail'],
        )
        users.append(user)


create_users(10 - len(users))
create_posts(200)


