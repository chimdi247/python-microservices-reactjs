from django.db import migrations


SAMPLE_PRODUCTS = [
    {'id': 1, 'title': 'Classic White Sneakers', 'image': 'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=600&q=80'},
    {'id': 2, 'title': 'Leather Backpack', 'image': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&q=80'},
    {'id': 3, 'title': 'Wireless Headphones', 'image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80'},
]


def seed_products(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    User = apps.get_model('products', 'User')

    # IDs match main-service's own seed exactly, so both databases agree
    # (the two services aren't otherwise kept in sync for a fresh seed —
    # see README.docker.md).
    for item in SAMPLE_PRODUCTS:
        Product.objects.get_or_create(
            id=item['id'],
            defaults={'title': item['title'], 'image': item['image'], 'likes': 0},
        )

    # UserAPIView picks `random.choice(User.objects.all())` for the "like"
    # feature's fake current-user lookup — with zero rows that call raises
    # IndexError, so make sure at least one exists.
    if not User.objects.exists():
        User.objects.create()


def remove_seed_products(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.filter(id__in=[item['id'] for item in SAMPLE_PRODUCTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_products, remove_seed_products),
    ]
