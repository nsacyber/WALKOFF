def main(steps, input_):
    input_ = int(input_)
    if steps[input_]:
        return steps[input_].output
    return None
