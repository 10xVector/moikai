"""Add current_period_end to User and define unique constraints at table level

Revision ID: c4d66dfb6a35
Revises: 2c623ae27cdb
Create Date: 2025-05-13 23:16:22.610395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4d66dfb6a35'
down_revision = '2c623ae27cdb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_period_end', sa.DateTime(), nullable=True))
        batch_op.alter_column('stripe_customer_id',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=120),
               existing_nullable=True)
        batch_op.alter_column('stripe_subscription_id',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=120),
               existing_nullable=True)
        batch_op.create_unique_constraint('uq_user_email', ['email'])
        batch_op.create_unique_constraint('uq_user_oauth_google_email', ['oauth_google_email'])
        batch_op.create_unique_constraint('uq_user_oauth_google_id', ['oauth_google'])
        batch_op.create_unique_constraint('uq_user_stripe_customer_id', ['stripe_customer_id'])
        batch_op.create_unique_constraint('uq_user_stripe_subscription_id', ['stripe_subscription_id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_stripe_subscription_id', type_='unique')
        batch_op.drop_constraint('uq_user_stripe_customer_id', type_='unique')
        batch_op.drop_constraint('uq_user_oauth_google_id', type_='unique')
        batch_op.drop_constraint('uq_user_oauth_google_email', type_='unique')
        batch_op.drop_constraint('uq_user_email', type_='unique')
        batch_op.alter_column('stripe_subscription_id',
               existing_type=sa.String(length=120),
               type_=sa.VARCHAR(length=100),
               existing_nullable=True)
        batch_op.alter_column('stripe_customer_id',
               existing_type=sa.String(length=120),
               type_=sa.VARCHAR(length=100),
               existing_nullable=True)
        batch_op.drop_column('current_period_end')

    # ### end Alembic commands ###
