from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
import requests

import pprint

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
# APPLICATION_NAME = "Restaurant Menu Application"

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

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state

    test = pprint.pformat(login_session)

    return render_template('login.html', STATE=state, test=test)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/')
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

@app.route('/item/add', methods=['GET', 'POST'])
def addItem():
    cats = session.query(Category).all()
    new_item = CategoryItem(name="", description="", category_id=-1)

    if request.method == 'POST':
        new_item.name = request.form['name']
        new_item.description = request.form['description']
        new_item.category_id = request.form['category']

        session.add(new_item)
        session.commit()

        return redirect(url_for('displayItemDetails', item_id= new_item.id))
    else:
        return render_template('item_edit.html', cats=cats, item=None)

@app.route('/item/<int:item_id>/delete', \
    methods=['GET', 'POST'])
def deleteItem(item_id):
    item = session.query(CategoryItem).join(CategoryItem.category) \
        .filter(CategoryItem.id==item_id).one()

    session.delete(item)
    session.commit()

    return redirect(url_for('displayItems'))
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
    app.secret_key = '1GrSamWXZ8ikGhg43UIUbw5X'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
