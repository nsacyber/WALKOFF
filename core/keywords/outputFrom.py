def main(actions, input_):
    input_ = int(input_)
    if actions[input_]:
        return actions[input_]._output.result
    return None
