from sqlalchemy import *

#Create an in memory db
db = create_engine('sqlite:///:memory:')
db.echo = False

metadata = BoundMetaData(db)

cachedobjects = Table('cachedobj', metadata)



