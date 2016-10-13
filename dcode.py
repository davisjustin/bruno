from datetime import timedelta


def arrayfy_ls(ls):
    return str(ls).replace('(', '[').replace(')', ']').replace("'", '"')


class BusTrip:

    def __init__(self, from_row, to_row):
        self.bus_id = []
        self.bus_dr = []
        for rw1 in from_row:
            for rw2 in to_row:
                if rw1[0] == rw2[0] and rw2[1] - rw1[1] > 0:
                    self.bus_id.append(rw1[0])
                    self.bus_dr.append(rw2[1] - rw1[1])

    def lq_bus_id(self):
        q_str = ""
        for item in self.bus_id:
            q_str += " " + item + ","
        return q_str[:-1]

    def get_schedule(self, trips_details):
        schedule = []
        for row in trips_details:
            time_elapsed = self.bus_dr[self.bus_id.index(row[0])]
            schedule.append([row[0], std_small(str(row[1])), std_small(str(row[1] + timedelta(minutes=time_elapsed)))])
        return schedule


def std_small(tm):
    hr, mn, ap = tm.split(':')
    hr = int(hr)
    if hr > 24 and int(mn) > 0:
        hr -= 24
    if hr >= 12:
        ap = ' PM'
        if hr > 12:
            hr -= 12
    else:
        ap = ' AM'
    if hr == 0:
        hr = 12
    if hr < 10:
        hr = "0" + str(hr)

    return str(hr) + ":" + mn + ap


def small_std(tm):
    tm, ap = tm.split(' ')
    hr, mn = tm.split(':')
    hr = int(hr)
    if ap == 'PM' and hr != 12:
        hr += 12
    if hr > 9:
        hr = str(hr)
    else:
        hr = "0" + str(hr)

    return hr + ":" + mn + ":00"
