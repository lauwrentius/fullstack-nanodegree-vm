from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Restaurant, Base, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

#restaurants = session.query(Restaurant).all()
#menu_items = session.query(MenuItem).all()

# for restaurant in restaurants:
#    print restaurant.name
#for menu_item in menu_items:
#    print menu_item.name



# veggieBurgers = session.query(MenuItem).filter_by(id='8').one()
#
# print veggieBurgers.name +'--'+ veggieBurgers.restaurant.name
# print veggieBurgers.price
#
# veggieBurgers.price = '$2.99'
#
# session.add(veggieBurgers)

# session.delete(veggieBurgers)

# session.commit()
#
# veggieBurgers = session.query(MenuItem).filter_by(name='Veggie Burger')
#
# for v in veggieBurgers:
#     print v.name +'--'+ v.restaurant.name
#     print v.price

def getRestaurants():
    restaurants = session.query(Restaurant).all()
    ret = ""

    for restaurant in restaurants:
        ret += '<p>'+restaurant.name + '<br />'
        ret +='<a href="#">EDIT</a><br />'
        ret +='<a href="#">DELETE</a></p>'

    return ret

def addRestaurants(restName):
    newRestaurant = Restaurant(name=restName)
    session.add(newRestaurant)
    session.commit()
