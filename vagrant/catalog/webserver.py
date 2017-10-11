from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem

app = Flask(__name__)

engine = create_engine('sqlite:///categoryitem.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# @app.route('/restaurants/<int:restaurant_id>/menu/JSON')
# def restaurantMenuJSON(restaurant_id):
#     restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
#     items = session.query(MenuItem).filter_by(
#         restaurant_id=restaurant_id).all()
#     return jsonify(MenuItems=[i.serialize for i in items])


# ADD JSON API ENDPOINT HERE


@app.route('/')
#@app.route('/restaurants/<int:restaurant_id>/menu')
def displayItems():
    cats = session.query(Category).all()
    items = session.query(CategoryItem).order_by(CategoryItem.id).all()
    title_text = "Latest Items"

    return render_template(
        'display_items.html', cats=cats, items=items,
        title_text=title_text, cat_name = "")

@app.route('/catalog/<int:cat_id>/')
def displaySingleCatItems(cat_id):
    cats = session.query(Category).all()
    curr_cat = session.query(Category).filter(Category.id==cat_id).one()
    items = session.query(CategoryItem) \
        .filter(CategoryItem.category_id==cat_id).all()

    title_text = "%s Items (%i items)" % (curr_cat.name, len(items))

    return render_template(
        'display_items.html', cats=cats, items=items,
        title_text=title_text, cat_name = curr_cat.name)

@app.route('/item/<int:item_id>')
def displayItemDetails(item_id):
    item = session.query(CategoryItem).join(CategoryItem.category) \
        .filter(CategoryItem.id==item_id).one()
    return render_template('item_details.html', item=item)

@app.route('/item/<int:item_id>/edit', \
    methods=['GET', 'POST'])
def editItem(item_id):
    cats = session.query(Category).all()
    item = session.query(CategoryItem).join(CategoryItem.category) \
        .filter(CategoryItem.id==item_id).one()

    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.category_id = request.form['category']

        session.add(item)
        session.commit()

        return redirect(url_for('displayItemDetails', item_id= item.id))
    else:
        return render_template('item_edit.html', cats=cats, item=item)

@app.route('/item/add', \
    methods=['GET', 'POST'])
def addItem():
    cats = session.query(Category).all()
    new_item = CategoryItem(name="", description="", category_id=-1)

    if request.method == 'POST':
        new_item.name = request.form['name']
        new_item.description = request.form['description']
        new_item.category_id = request.form['category']

        session.add(new_item)
        session.commit()
        # session.refresh(new_item)

        return 'xxx'#new_item#redirect(url_for('displayItemDetails', item_id= new_item.id))
    else:
        return render_template('item_edit.html', cats=cats, item=None)

# @app.route('/restaurants/<int:restaurant_id>/new', methods=['GET', 'POST'])
# def newMenuItem(restaurant_id):
#
#     if request.method == 'POST':
#         newItem = MenuItem(name=request.form['name'], description=request.form[
#                            'description'], price=request.form['price'], course=request.form['course'], restaurant_id=restaurant_id)
#         session.add(newItem)
#         session.commit()
#         return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
#     else:
#         return render_template('newmenuitem.html', restaurant_id=restaurant_id)
#
#
# @app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/edit',
#            methods=['GET', 'POST'])
# def editMenuItem(restaurant_id, menu_id):
#     editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
#     if request.method == 'POST':
#         if request.form['name']:
#             editedItem.name = request.form['name']
#         if request.form['description']:
#             editedItem.description = request.form['name']
#         if request.form['price']:
#             editedItem.price = request.form['price']
#         if request.form['course']:
#             editedItem.course = request.form['course']
#         session.add(editedItem)
#         session.commit()
#         return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
#     else:
#
#         return render_template(
#             'editmenuitem.html', restaurant_id=restaurant_id, menu_id=menu_id, item=editedItem)
#
#
# @app.route('/restaurants/<int:restaurant_id>/<int:menu_id>/delete',
#            methods=['GET', 'POST'])
# def deleteMenuItem(restaurant_id, menu_id):
#     itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
#     if request.method == 'POST':
#         session.delete(itemToDelete)
#         session.commit()
#         return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
#     else:
#         return render_template('deleteconfirmation.html', item=itemToDelete)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
