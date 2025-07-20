"""
This file defines the database tables
"""

from .common import db, Field

def get_user_email():
    """Get current user email (used in views)"""
    auth = db.auth.user
    return auth.email if auth else None

# Category table definition
db.define_table(
    'category',
    Field('name', 'string', unique=True),  # Category name
)

# Item table definition with category_id reference
db.define_table(
    'item',
    Field('name', 'string'),  # Item name
    Field('quantity', 'integer', default=1),  # Quantity of the item
    Field('category_id', 'reference category', default=None),  # Reference to category
)
