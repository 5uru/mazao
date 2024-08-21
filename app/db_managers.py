from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker


# Create a base class for declarative class definitions
Base = declarative_base()


# Define the ManagementZone model
class ManagementZone(Base):
    __tablename__ = "management_zones"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    crop_type = Column(String)
    longitude = Column(Float)
    latitude = Column(Float)

    def __repr__(self):
        return f"<ManagementZone(name='{self.name}', crop_type='{self.crop_type}', location=({self.longitude}, {self.latitude}))>"


# Define Event model
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    date = Column(String, nullable=False)
    type = Column(String)
    description = Column(String)
    management_zone_id = Column(Integer, ForeignKey("management_zones.id"))

    def __repr__(self):
        return f"<Event(name='{self.name}', date='{self.date}', type='{self.type}',  description='{self.description}' management_zone_id={self.management_zone_id})>"


# Create an engine that stores data in the local directory's
# management_zones.db file.
engine = create_engine("sqlite:///databases.db")

# Create all tables in the engine
Base.metadata.create_all(engine)

# Create a session maker
Session = sessionmaker(bind=engine)


def add_management_zone(name, crop_type, longitude, latitude):
    # Create a session
    session = Session()

    # Create a new ManagementZone object
    new_zone = ManagementZone(
        name=name, crop_type=crop_type, longitude=longitude, latitude=latitude
    )

    # Add the new zone to the session
    session.add(new_zone)

    # Commit the transaction
    session.commit()

    # Close the session
    session.close()

    return new_zone


def get_management_zones():
    session = Session()
    try:
        return session.query(ManagementZone).all()
    except Exception as e:
        print(f"An error occurred while retrieving: {e}")
        return []
    finally:
        session.close()


def delete_management_zone(zone_id):
    session = Session()
    try:
        if zone := session.query(ManagementZone).filter_by(id=zone_id).first():
            session.delete(zone)
            session.commit()
            print(f"Deleted management zone: {zone}")
        else:
            print(f"No management zone found with id: {zone_id}")
    except Exception as e:
        print(f"An error occurred while deleting: {e}")
        session.rollback()
    finally:
        session.close()


def add_event(name, date, management_zone_id, event_type, description):
    session = Session()
    try:
        new_event = Event(
            name=name, date=date, type=event_type, management_zone_id=management_zone_id, description=description
        )
        session.add(new_event)
        session.commit()
        return new_event
    except Exception as e:
        print(f"An error occurred while adding event: {e}")
        session.rollback()
    finally:
        session.close()


def get_events():
    session = Session()
    try:
        return session.query(Event).all()
    except Exception as e:
        print(f"An error occurred while retrieving events: {e}")
        return []
    finally:
        session.close()


def get_events_by_zone(zone_id):
    session = Session()
    try:
        return session.query(Event).filter_by(management_zone_id=zone_id).all()
    except Exception as e:
        print(f"An error occurred while retrieving events: {e}")
        return []
    finally:
        session.close()

def delete_all_zone_events(zone_id):
    session = Session()
    try:
        session.query(Event).filter_by(management_zone_id=zone_id).delete()
        session.commit()
    except Exception as e:
        print(f"An error occurred while deleting events: {e}")
        session.rollback()
    finally:
        session.close()
def delete_all_zone_events_by_type(zone_id, event_type):
    session = Session()
    try:
        session.query(Event).filter_by(management_zone_id=zone_id, type=event_type).delete()
        session.commit()
    except Exception as e:
        print(f"An error occurred while deleting events: {e}")
        session.rollback()
    finally:
        session.close()