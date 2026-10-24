from django.db import migrations


def backfill_product_names(apps, schema_editor):
    OrderItem = apps.get_model('store', 'OrderItem')
    db_alias = schema_editor.connection.alias
    for item in OrderItem.objects.using(db_alias).filter(product_name='').select_related('product').iterator():
        if item.product_id and item.product:
            item.product_name = item.product.name
            item.save(update_fields=['product_name'], using=db_alias)


class Migration(migrations.Migration):
    dependencies = [('store', '0003_alter_order_payment_method')]
    operations = [migrations.RunPython(backfill_product_names, migrations.RunPython.noop)]
