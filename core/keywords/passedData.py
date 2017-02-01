def main(steps, args):
    if args["id"] in steps:
        if "prePlayData" in steps[args["id"]].input:
            return steps[args["id"]].input["prePlayData"]
    else:
        return ""