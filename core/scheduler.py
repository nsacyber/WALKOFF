import datetime

def readyPlays(plays):
    results = []
    current = datetime.datetime.now()
    for play in plays:
        schedule = plays[play].getOption("scheduler")
        autorun = plays[play].getOption("autorun")

        if autorun == "true":
            start = datetime.datetime.strptime(schedule["sDT"], "%Y-%m-%d %H:%M:%S")
            end = datetime.datetime.strptime(schedule["eDT"], "%Y-%m-%d %H:%M:%S")

            #Tests Date Range
            if start <= current <= end:
                #Tests Time Range
                if plays[play].getLastRun() <= datetime.datetime.strptime("1900-1-1 1:1:1", "%Y-%m-%d %H:%M:%S") or schedule["interval"] < 0:
                    results.append(play)
                else:
                    diff = current - plays[play].getLastRun()
                    if float(diff.total_seconds()/60) >= schedule["interval"]:
                        results.append(play)

    return results