def main(steps, input):
    input = int(input)
    if steps[input]:
        return steps[input].output
    return None
