def main(steps, input):
    input = str(input)
    if steps[input]:
        return steps[input].output
    return None
