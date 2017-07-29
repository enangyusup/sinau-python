#!/usr/bin/env python

from datetime import datetime, timedelta

from lxml import etree
from bottle import request, response, route, run

from models import Alert, Team, Stadium, Official, Player, Match, \
                   LineUp, EventType, EventSubType, Event, Video, \
                   Phase, Statistic, Session


@route('/champions', method='POST')
def champions():
    if request.files:
        xml = request.files.value
    else:
        xml = request.body

    # db session dijadiin global karena yang bikin males
    global session
    session = Session()
    code = xmlparse(xml)
    session.close()

    response.add_header('code', code)
    return


def xmlparse(xml):
    """parsing xml yang diterima
    return code: 0 = sukses, 1 = invalid xml, 2 = invalid content,
                 3 = duplikat, 4 = invalid match, 5 = alert terlambat"""
    try:
        root = etree.parse(xml)
    except etree.XMLSyntaxError:
        return 1

    x_root = root.getroot()

    # notifikasi video dibuka dengan <match>
    # yang lain dibuka dengan <message>
    if x_root.tag == 'match':
        if not current_match():
            return 4
        match = session.query(Match).filter_by(id=x_root.get('id')).first()
        video = process_video(match, x_root)
        if not video:
            return 2
        return 0

    # di dalam message, type & idmessage harus ada atau hentikan!
    if 'type' not in x_root.keys() or 'idmessage' not in x_root.keys():
        return 2

    # kalau alert sudah tercatat di db, tolak!
    x_msg_id = x_root.get('idmessage')
    alert = session.query(Alert).filter_by(id=x_msg_id).first()
    if alert is not None:
        return 3

    # TODO: how to process this?
    if not current_match():
        return 4

    # pertama dapatkan dulu match yang berlangsung
    x_match = x_root.find('match')
    match = process_match(x_match)

    # baru proses alert yang ada, bedakan berdasar type
    x_type = x_root.get('type')
    events = ['Goal', 'Penalty', 'RedCard', 'YellowCard', 'Substitution']
    phases = ['Half', '2ndHalf', '1stExtra', '2ndExtra', 'Full']

    # Line-Ups
    if x_type == 'Line-Up':
        process_lineup(x_root.find('lineup'))

    # Events
    elif x_type in events:
        if obsolete_alert(x_root, 'event'):
            return 5
        event = process_event(match, x_root.find('events'))
        if not event:
            return 2

    # Statistics
    elif x_type in phases:
        if obsolete_alert(x_root, 'phase'):
            return 5
        stat = process_statistic(match, x_type, x_root.find('statistics'))
        if not stat:
            return 2

    # Start* => ignore
    elif x_type.startswith('Start'):
        pass

    # selesai tanpa masalah, masukin id alert ke history
    alert = Alert(id=x_msg_id, time=datetime.now(), type=x_type)
    session.add(alert)
    session.commit()

    # and good bye, have a nice life.
    return 0


def get_or_create(model, **kwargs):
    """kalau data ada di db, ambil. kalau gak ada, buat."""
    obj = session.query(model).filter_by(**kwargs).first()
    if obj:
        return obj
    obj = model(**kwargs)
    session.add(obj)
    session.commit()
    return obj


def current_match():
    """cek pertandingan bener hari ini gak"""
    return True


def obsolete_alert(x_root, _type):
    """cek apakah pesan yang diterima sudah telat"""
    x_match_id = x_root.find('match').get('code')

    # di dalam alert event, ada id babaknya...
    if _type == 'event':
        phase_id = x_root.xpath('events/event/time')[0].get('phase')

    # tapi gak ada dalam alert phase, jadi mesti baca namanya dari type,
    # dan cari idnya di db.
    elif _type == 'phase':
        _phase = session.query(Phase).filter_by(name=x_root.get('type')).first()
        phase_id = _phase.id

    stat = session.query(Statistic).filter_by(match_id=x_match_id,
                                              phase_id=phase_id).first()

    # kalau babak ini sudah ada di statistik, berarti data beneran telat.
    if stat is not None:
        return True
    return False


def process_match(x_match):
    """process match data"""
    # team
    x_teams = x_match.findall('team')
    for x_team in x_teams:
        if x_team.get('team') == 'Home':
            home = get_or_create(Team, id=x_team.get('code'),
                                       name=x_team.get('name'),
                                       fullname=x_team.text)
        elif x_team.get('team') == 'Away':
            away = get_or_create(Team, id=x_team.get('code'),
                                       name=x_team.get('name'),
                                       fullname=x_team.text)
    # stadium
    x_stadium = x_match.find('stadium')
    x_venue = x_match.find('venue')
    stadium = get_or_create(Stadium, id=x_stadium.get('code'),
                                     name=x_stadium.text,
                                     country=x_venue.get('country'),
                                     city=x_venue.text)

    # official
    x_official = x_match.find('official')
    official = get_or_create(Official, type=x_official.get('type').lower(),
                                       name=x_official.text,
                                       nationality=x_official.get('nat'))

    # time, asumsi CET = UTC+1, perbedaan dengan jakarta 6 jam.
    x_date = x_match.get('date')
    x_time = x_match.get('time')
    r_time = datetime.strptime(x_date + x_time, '%d/%m/%Y%H:%M')
    time = r_time + timedelta(0, 6 * 3600)

    # de match!
    match = get_or_create(Match, id=x_match.get('code'),
                                 session=x_match.get('session'),
                                 round=x_match.get('round'),
                                 group=x_match.get('group'),
                                 time=time,
                                 home=home,
                                 away=away,
                                 stadium=stadium,
                                 official=official)
    return match


def process_lineup(x_lineup):
    """process lineup"""
    # dalam setiap pertandingan ada 2 team, kalau tidak, namanya latihan.
    x_teams = x_lineup.findall('team')
    for x_team in x_teams:
        team = session.query(Team).filter_by(id=x_team.get('code')).first()
        x_players = x_team.findall('player')
        for x_player in x_players:
            # beresin dulu urusan player
            goalkeeper = True if x_player.get('goalkeeper') == 'Y' else False
            player = get_or_create(Player, id=x_player.get('code'),
                                           name=x_player.get('name'),
                                           fullname=x_player.text,
                                           goalkeeper=goalkeeper)
            # baru masukin ke line up
            bench = True if x_player.get('bench') == 'Y' else False
            get_or_create(LineUp, number=x_player.get('number'),
                                  bench=bench,
                                  team=team,
                                  player=player)
    return


def process_event(match, x_events):
    """process event"""
    # cari dulu di db, id event yang terjadi
    x_event = x_events.find('event')
    type = session.query(EventType).filter_by(name=x_event.get('type')).first()

    # question: kenapa subtype kiriman kadang ada spasi di sampingnya?
    x_subtype = x_event.get('subtype').strip()
    if x_subtype:
        subtype = session.query(EventSubType).filter_by(name=x_subtype).first()
    else:
        subtype = None

    # siapa pelakunya..
    x_player = x_event.find('player')
    player = session.query(Player).filter_by(id=x_player.get('code')).first()

    # playerin cuma ada di satu event: pergantian pemain
    x_playerin = x_event.find('playerin')
    if x_playerin is not None:
        playerin = session.query(Player).filter_by(id=x_playerin.get('code')).first()
    else:
        playerin = None

    # menit ke berapa event ini terjadi
    x_time = x_event.find('time')
    phase = session.query(Phase).filter_by(id=x_time.get('phase')).first()

    # dan masukkan ke db
    try:
        event = Event(id=x_event.get('code'),
                      match=match,
                      type=type,
                      subtype=subtype,
                      player=player,
                      playerin=playerin,
                      phase=phase,
                      minute=x_time.get('minute'),
                      score=x_event.get('score'),
                      penalty=x_event.get('penalty'))
        session.add(event)
        session.commit()
    except:
        # question: kenapa kalau gagal dikirim False?
        # answer: karena yang bikin gak punya ide lain
        return False
    return True


def process_video(match, x_video):
    """process data video"""
    # video yang didapat bisa berkaitan dengan event yang terjadi, bisa tidak.
    # kalau ada kaitannya, hubungkan dengan id event terkait.
    x_event_id = x_video.find('message').get('actionid')
    if x_event_id != '0':
        event = session.query(Event).filter_by(id=x_event_id).first()
    else:
        event = None

    try:
        video = Video(match=match,
                      event=event,
                      code=x_video.get('idmessage'),
                      type=x_video.find('message').text,
                      title=x_video.find('title').text,
                      version=x_video.find('version').text,
                      length=x_video.find('message').get('subtype'),
                      size=x_video.find('size').text,
                      url=x_video.find('url').text)
        session.add(video)
        session.commit()
    except:
        return False
    return True


def process_statistic(match, x_type, x_statistics):
    """process statistic"""
    # statistik yang ada untuk babak yang mana?
    phase = session.query(Phase).filter_by(name=x_type).first()

    # team:
    home_team = session.query(Team).filter_by(id=match.home_id).first()
    away_team = session.query(Team).filter_by(id=match.away_id).first()

    # question: how to make this cleaner?
    for x_statistic in x_statistics.findall('statistic'):
        xs_type = x_statistic.get('type')
        xs_home = x_statistic.get('home')
        xs_away = x_statistic.get('away')
        if xs_type == 'yellowCard':
            home_yellowcard = xs_home
            away_yellowcard = xs_away
        elif xs_type == 'redCard':
            home_redcard = xs_home
            away_redcard = xs_away
        elif xs_type == 'goal':
            home_goal = xs_home
            away_goal = xs_away
        elif xs_type == 'shotsWide':
            home_shotswide = xs_home
            away_shotswide = xs_away
        elif xs_type == 'shotsGoal':
            home_shotsgoal = xs_home
            away_shotsgoal = xs_away
        elif xs_type == 'corner':
            home_corner = xs_home
            away_corner = xs_away
        elif xs_type == 'offside':
            home_offside = xs_home
            away_offside = xs_away
        elif xs_type == 'possessionTime':
            home_posstime = xs_home
            away_posstime = xs_away
        elif xs_type == 'possessionPerc':
            home_possperc = xs_home
            away_possperc = xs_away

    try:
        home_stat = Statistic(match=match,
                              phase=phase,
                              team=home_team,
                              yellowcard=home_yellowcard,
                              redcard=home_redcard,
                              goal=home_goal,
                              shotswide=home_shotswide,
                              shotsgoal=home_shotsgoal,
                              corner=home_corner,
                              offside=home_offside,
                              posstime=home_posstime,
                              possperc=home_possperc)

        away_stat = Statistic(match=match,
                              phase=phase,
                              team=away_team,
                              yellowcard=away_yellowcard,
                              redcard=away_redcard,
                              goal=away_goal,
                              shotswide=away_shotswide,
                              shotsgoal=away_shotsgoal,
                              corner=away_corner,
                              offside=away_offside,
                              posstime=away_posstime,
                              possperc=away_possperc)

        session.add_all([home_stat, away_stat])
        session.commit()
    except:
        return False
    return True

run(host='0.0.0.0', port=8080, server='waitress')
