"""Add cascade delete to card exercises

Revision ID: c8ce729ecc1a
Revises: 465a943cd127
Create Date: 2025-05-21 21:46:03.898

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8ce729ecc1a'
down_revision = '465a943cd127'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing foreign key constraint
    op.drop_constraint('user_exercise_card_id_fkey', 'user_exercise', type_='foreignkey')
    
    # Add the new foreign key constraint with cascade delete
    op.create_foreign_key(
        'user_exercise_card_id_fkey',
        'user_exercise', 'card',
        ['card_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Drop the cascade delete foreign key
    op.drop_constraint('user_exercise_card_id_fkey', 'user_exercise', type_='foreignkey')
    
    # Add back the original foreign key without cascade
    op.create_foreign_key(
        'user_exercise_card_id_fkey',
        'user_exercise', 'card',
        ['card_id'], ['id']
    )
