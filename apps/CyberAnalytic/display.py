
def load(*args, **kwargs):
    from apps.CyberAnalytic.main import suspicious_pids, threat_pid
    #sus_pids = [threat_pid('aaa', 'bbb', 'ccc'), threat_pid('111', '222', 'xxx'), threat_pid('akaf', '15', 'exe')]
    #return {'pids': [x._asdict() for x in sus_pids]}
    return {'pids': [x._asdict() for x in suspicious_pids]}
