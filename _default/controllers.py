"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from yatl.helpers import A

from py4web import URL, abort, action, redirect, request

from .common import (
    T,
    auth,
    authenticated,
    cache,
    db,
    flash,
    logger,
    session,
    unauthenticated,
)

def get_or_create_category(category_name):
    """Get existing category by name or create a new one"""
    # Try to find the category
    category_record = db(db.category.name == category_name).select().first()
    if not category_record:
        # Category doesn't exist, create it
        category_id = db.category.insert(name=category_name)
        redirect(URL('index', vars=dict(category=category_name)))
    else:
        return category_record.id

@action("index")
@action.uses("index.html", auth, T)
def index():
    """Show items in their categories"""
    # Get all available categories
    categories = db(db.category).select()

    # Get current category name from URL parameter or use default
    category_name = request.params.get('category', 'default_list')

    # Ensure we have a valid category - this will create the category if it doesn't exist
    category_id = get_or_create_category(category_name)

    # Get all items for this category
    items = db((db.item.category_id == category_id) |
               (db.item.category_id == None)).select(orderby=db.item.name)

    return dict(items=items, title=category_name, categories=categories)

@action('item/add', method=['POST'])
@action.uses(db, auth, session, 'partials/item_row.html')
def add_item():
    """Add a new item to a category or update quantity if it already exists"""
    name = request.params.get('name')

    # Get category name from URL parameter
    category_name = request.params.get('category', 'default_list')
    category_id = get_or_create_category(category_name)

    # Check if item already exists in this category
    item = db((db.item.name == name) & (db.item.category_id == category_id)).select().first()
    if item:
        # Item exists, increment quantity
        db(db.item.id == item.id).update(quantity=item.quantity + 1)
    else:
        # New item, add with quantity 1
        db.item.insert(name=name, category_id=category_id)

    # Return the updated table body for htmx to update the DOM
    items = db((db.item.category_id == category_id) |
               (db.item.category_id == None)).select(orderby=db.item.name)
    return dict(items=items)

@action('item/change_quantity', method=['POST'])
@action.uses(db, auth, session)
def change_quantity():
    """Change the quantity of an existing item"""
    item_id = request.params.get('id')
    delta = int(request.params.get('delta'))
    category_name = request.params.get('category', 'default_list')

    # Get current item
    item = db(db.item.id == item_id).select().first()
    if not item:
        return "Error: Item not found"

    # Calculate new quantity with minimum of 0
    new_quantity = max(0, item.quantity + delta)
    db(db.item.id == item_id).update(quantity=new_quantity)

    # Return only the new quantity for htmx to update the DOM
    return str(new_quantity)

@action('item/delete', method=['POST'])
@action.uses(db, auth, session)
def delete_item():
    """Delete an existing item"""
    item_id = request.params.get('id')
    category_name = request.params.get('category', 'default_list')

    # Get current item
    item = db(db.item.id == item_id).select().first()
    if not item:
        return "Error: Item not found"

    # Delete the item
    db(db.item.id == item_id).delete()

    # Return an empty string to indicate success (the row will be removed from DOM)
    return ""

@action('category/delete', method=['POST'])
@action.uses(db, auth, session)
def delete_category():
    """Delete a category and all its items"""
    category_name = request.params.get('category')

    # Get the category ID
    category_record = db(db.category.name == category_name).select().first()
    if not category_record:
        return "Error: Category not found"

    category_id = category_record.id

    # Delete all items in this category first
    db((db.item.category_id == category_id)).delete()

    # Then delete the category itself
    db(db.category.id == category_id).delete()

    # Redirect to the first available category or create a new default category
    available_categories = db(db.category).select()
    if available_categories:
        redirect(URL('index', vars=dict(category=available_categories[0].name)))
    else:
        # Create a new default category and redirect to it
        db.category.insert(name='default_list')
        redirect(URL('index', vars=dict(category='default_list')))
