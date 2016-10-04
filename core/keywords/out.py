

def main(steps, args):
    if args["id"] in steps:
        step = steps[args["id"]]
        return step.out[step.device[0]]
    else:
        return ""