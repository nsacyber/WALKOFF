from core.decorators import flag
import time

@flag
def timeCompare(value, operator, currentTime = None):

    if currentTime is None:
    	currentTime = time.time()

    if operator == 'g' and value > currentTime:
        return True

    elif operator == 'ge' and value >= currentTime:
        return True

    elif operator == 'l' and value < currentTime:
        return True

    elif operator == 'le' and value <= currentTime:
        return True

    elif operator == 'e' and value == currentTime:
        return True
    else:
      	return None