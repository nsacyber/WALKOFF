from core.decorators import flag


@flag
def count(value, operator, threshold):
    if operator == 'g' and value > threshold:
        return True

    elif operator == 'ge' and value >= threshold:
        return True

    elif operator == 'l' and value < threshold:
        return True

    elif operator == 'le' and value <= threshold:
        return True

    elif operator == 'e' and value == threshold:
        return True
    else:
        return value == threshold
