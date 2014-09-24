from cartodb import CartoDBAPIKey, CartoDBException

#Boilerplate connection as per the docs
user = 'jlaura@asu.edu'
API_KEY = 'b567072ead5c2e9ea1fe2aef381851f86d874644'
cartodb_domain = 'jlaura'  # I am guess here
cl = CartoDBAPIKey(API_KEY, cartodb_domain)


def gettable(tablename, format='geojson'):
    """
    Connect to a CartoDB account and get the selected table as geojson
    """
    query = "SELECT * FROM {}".format(tablename)
    print query
    try:
        return cl.sql(query, format=format)
    except CartoDBException as err:
        return "Some error occurred:{}".format(err)

def gettablelist():
    """
    Gets a listing of all of the tables in the account by name
    """
    try:
        return cl.sql('SELECT * FROM information_schema.tables')
    except CartoDBException as err:
        return "Some error occurred: {}".format(err)

if __name__ == '__main__':
    print gettable('columbus')
