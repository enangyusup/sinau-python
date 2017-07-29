#!/usr/bin/env python

from sys import argv
from models import *

db = Session()

def create():
    Base.metadata.create_all(bind=engine)

    db.add_all([
        EventType(name='Goal'),
        EventType(name='Penalty'),
        EventType(name='RedCard'),
        EventType(name='YellowCard'),
        EventType(name='Substitution')
        ])

    db.add_all([
        EventSubType(name='Own', desc='Own Goal'),
        EventSubType(name='O', desc='Scored'),
        EventSubType(name='X', desc='Missed')
        ])

    db.add_all([
        Phase(id=1, name='Half', desc="First Half"),
        Phase(id=2, name='2ndHalf', desc="Second Half"),
        Phase(id=3, name='1stExtra', desc="First Additional Half"),
        Phase(id=4, name='2ndExtra', desc="Second Additional Half"),
        Phase(id=5, name='Penalties', desc="Penalties"),
        Phase(id=6, name='Full', desc="Complete")
        ])

    db.commit()


def drop():
    Base.metadata.drop_all(bind=engine)


if __name__ == '__main__':
    if argv[1] == 'create':
        create()
    elif argv[1] == 'drop':
        drop()
    else:
        print 'embek'
