"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, Response, render_template, request, session, redirect, url_for, jsonify
from flaskext.mysql import MySQL

import dcode

app = Flask(__name__)
app.secret_key = 'secret key!!'

flag_online = True

if flag_online:
    app.config['MYSQL_DATABASE_HOST'] = '52.74.77.8'
    app.config['MYSQL_DATABASE_USER'] = 'sql6140018'
    app.config['MYSQL_DATABASE_PASSWORD'] = 'c2LLhiRL7D'
    app.config['MYSQL_DATABASE_DB'] = 'sql6140018'
    print('set to online DB')
else:
    app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
    app.config['MYSQL_DATABASE_USER'] = 'root'
    app.config['MYSQL_DATABASE_PASSWORD'] = ''
    app.config['MYSQL_DATABASE_DB'] = 'bruno'
    print('set to local DB')

flag_db_fail = False
try:
    sq = MySQL()
    sq.init_app(app)
    sq_connect = sq.connect()
    sq_cursor = sq_connect.cursor()
    print('connected to DB')
except:
    print('failed to connect to DB')
    flag_db_fail = True

wsgi_app = app.wsgi_app


@app.route('/')
def root():
    if flag_db_fail:
        return render_template('Error.html', ErrMsg='Online DB Connect Error')

    loc_from = request.args.get('loc_from')
    loc_dest = request.args.get('loc_dest')

    # get details to auto fill search box
    query = "select distinct stop_name from route_details"
    sq_cursor.execute(query)
    rows = sq_cursor.fetchall()
    ac_list = list()
    for row in rows:
        ac_list.append(row[0])

    if loc_from is not None and loc_dest is not None:

        # get details and time elapsed for bus passing through start point
        query = "select id_bus, elp_time from route_details where stop_name like '" + loc_from + "';"
        sq_cursor.execute(query)
        rows_from = sq_cursor.fetchall()
        # get details and time elapsed for bus passing through end point
        query = "select id_bus, elp_time from route_details where stop_name like '" + loc_dest + "';"
        sq_cursor.execute(query)
        rows_to = sq_cursor.fetchall()

        # instantiate object with from and to details and IF there is any buses passing through the from and to, go...
        bt = dcode.BusTrip(rows_from, rows_to)
        if bt.bus_id:
            query = "select * from trips where id_bus in (" + bt.lq_bus_id() + ");"
            sq_cursor.execute(query)
            search_result = bt.get_schedule(sq_cursor.fetchall())

            return render_template("home.html",
                                   auto_comp_list=ac_list,
                                   bus_start_point=loc_from,
                                   bus_end_point=loc_dest,
                                   res_data=search_result)
        # ELSE return page with 'no bus found' message
        else:
            return render_template("home.html",
                                   auto_comp_list=ac_list,
                                   no_bus=True,
                                   no_result=True)

    return render_template("home.html",
                           auto_comp_list=ac_list,
                           no_result=True)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        un = request.form['username']
        pw = request.form['password']

        sq_cursor.execute("select * from user_table where unm like '" + un + "' and pwd like '" + pw + "'")
        result = sq_cursor.fetchone()

        if result is None:
            return redirect(url_for('login'))
        else:
            session['username'] = un
            return redirect(url_for('dashboard'))
    else:
        return render_template("login.html")


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' in session:
        if request.method == 'POST':
            task = request.form['task']
            if task is not None:
                if task == 'add-schedule':
                    try:
                        new_bus_id = request.form['bus-id']
                        new_bus_point = request.form['bus-stop']
                        new_point_time = request.form['bus-stop-time']
                        query = "INSERT INTO route_details VALUES " \
                                "('" + new_bus_id + "', '" + new_bus_point + "', '" + new_point_time + "')"
                        sq_cursor.execute(query)
                        sq_connect.commit()
                    except Exception as e:
                        print('Exception @ add-schedule > ' + str(e))
                elif task == 'add-trip':
                    try:
                        trip_bus = request.form['trip-bus']
                        trip_time = request.form['trip-time']
                        trip_time = dcode.small_std(trip_time)
                        query = "INSERT INTO trips VALUES ('" + trip_bus + "', '" + trip_time + "')"
                        sq_cursor.execute(query)
                        sq_connect.commit()
                    except Exception as e:
                        print('Exception @ trip-bus > ' + str(e))
                elif task == 'del-bus':
                    try:
                        del_bus = request.form['bus-id']
                        query = "delete from trips where id_bus like '" + del_bus + "';"
                        query += "delete from route_details where id_bus like '" + del_bus + "';"
                        sq_cursor.execute(query)
                        sq_connect.commit()
                    except Exception as e:
                        print('Exception > ' + str(e))
                elif task == 'del-schedule':
                    try:
                        sc_id, bus_schedule = request.form['bus-schedule'].split('/')
                        query = "delete from route_details where " \
                                "id_bus like '" + sc_id + "' and elp_time like '" + bus_schedule + "'"
                        sq_cursor.execute(query)
                        sq_connect.commit()
                    except Exception as e:
                        print('Exception @ del-schedule > ' + str(e))
                elif task == 'del-trip':
                    try:
                        tp_id, bus_trip = request.form['bus-trip'].split('/')
                        bus_trip = dcode.small_std(bus_trip)
                        query = "delete from trips where " \
                                "id_bus like '" + tp_id + "' and start_time like '" + bus_trip + "'"
                        sq_cursor.execute(query)
                        sq_connect.commit()
                    except Exception as e:
                        print('Exception @ del-trip > ' + str(e))
                else:
                    print('dashboard-post: unknown-task!')

            return redirect(url_for('dashboard'))

        query = "select distinct id_bus from route_details ORDER BY id_bus"
        sq_cursor.execute(query)
        rows = sq_cursor.fetchall()
        bus_ids = list()
        for row in rows:
            bus_ids.append(row[0])

        query = "select distinct stop_name from route_details"
        sq_cursor.execute(query)
        rows = sq_cursor.fetchall()
        stop_names = list()
        for row in rows:
            stop_names.append(row[0])

        return render_template('dashboard.html', bus_ids=bus_ids, stop_names=stop_names)
    else:
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('root'))


@app.route('/ajax')
def ajax():
    if 'username' in session:
        sel_bus_id = request.args.get('sel_bus_id', 'default_none', type=str)
        query = 'select stop_name, elp_time from route_details where id_bus like "' + sel_bus_id + '" ORDER BY elp_time'
        sq_cursor.execute(query)
        rows_schedule = sq_cursor.fetchall()
        query = 'select start_time from trips where id_bus like "' + sel_bus_id + '" ORDER BY start_time'
        sq_cursor.execute(query)
        rows_trips = sq_cursor.fetchall()

        list_schedule = []
        for row in rows_schedule:
            list_schedule.append(row)
        list_trips = []
        for row in rows_trips:
            list_trips.append(dcode.std_small(str(row[0])))

        result = dcode.arrayfy_ls([list_schedule, list_trips])
        return result
    else:
        return None


if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT, debug=True)
