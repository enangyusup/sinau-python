from sqlalchemy import create_engine
from sqlalchemy import Boolean, Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


engine = create_engine(
            "mysql://enang:yusup@127.0.0.1/champions",
            pool_recycle=280,
             connect_args={'reconnect': True})
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True, autoincrement=False)
    time = Column(DateTime)
    type = Column(String(20))


class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(50))
    fullname = Column(String(100))


class Stadium(Base):
    __tablename__ = 'stadiums'
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(50))
    country = Column(String(5))
    city = Column(String(50))


class Official(Base):
    __tablename__ = 'officials'
    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    name = Column(String(50))
    nationality = Column(String(5))


class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(50))
    fullname = Column(String(100))
    goalkeeper = Column(Boolean)


class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True, autoincrement=False)
    session = Column(Integer)
    round = Column(Integer)
    group = Column(String(5))
    time = Column(DateTime)
    home_id = Column(Integer, ForeignKey('teams.id'))
    away_id = Column(Integer, ForeignKey('teams.id'))
    stadium_id = Column(Integer, ForeignKey('stadiums.id'))
    official_id = Column(Integer, ForeignKey('officials.id'))
    home = relationship('Team', primaryjoin=(home_id == Team.id))
    away = relationship('Team', primaryjoin=(away_id == Team.id))
    stadium = relationship('Stadium')
    official = relationship('Official')


class LineUp(Base):
    __tablename__ = 'lineups'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    player_id = Column(Integer, ForeignKey('players.id'))
    number = Column(Integer)
    bench = Column(Boolean)
    team = relationship('Team')
    player = relationship('Player')


class EventType(Base):
    __tablename__ = 'event_types'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))


class EventSubType(Base):
    __tablename__ = 'event_subtypes'
    id = Column(Integer, primary_key=True)
    name = Column(String(5))
    desc = Column(String(20))


class Phase(Base):
    __tablename__ = 'phase'
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(10))
    desc = Column(String(30))


class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, autoincrement=False)
    match_id = Column(Integer, ForeignKey('matches.id'))
    type_id = Column(Integer, ForeignKey('event_types.id'))
    subtype_id = Column(Integer, ForeignKey('event_subtypes.id'))
    player_id = Column(Integer, ForeignKey('players.id'))
    playerin_id = Column(Integer, ForeignKey('players.id'))
    phase_id = Column(Integer, ForeignKey('phase.id'))
    minute = Column(Integer)
    score = Column(String(5))
    penalty = Column(String(5))
    match = relationship('Match')
    type = relationship('EventType')
    subtype = relationship('EventSubType')
    player = relationship('Player', primaryjoin=player_id == Player.id)
    playerin = relationship('Player', primaryjoin=playerin_id == Player.id)
    phase = relationship('Phase')


class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'))
    event_id = Column(Integer, ForeignKey('events.id'))
    type = Column(String(50))
    code = Column(Integer)
    title = Column(String(100))
    version = Column(Integer)
    length = Column(Integer)
    size = Column(Integer)
    url = Column(String(400))
    match = relationship('Match')
    event = relationship('Event')


class Statistic(Base):
    __tablename__ = 'statistics'
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'))
    phase_id = Column(Integer, ForeignKey('phase.id'))
    team_id = Column(Integer, ForeignKey('teams.id'))
    yellowcard = Column(Integer)
    redcard = Column(Integer)
    goal = Column(Integer)
    shotswide = Column(Integer)
    shotsgoal = Column(Integer)
    corner = Column(Integer)
    offside = Column(Integer)
    posstime = Column(Integer)
    possperc = Column(Integer)
    match = relationship('Match')
    phase = relationship('Phase')
    team = relationship('Team')
