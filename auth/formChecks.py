from wtforms.validators import ValidationError
import json

#Custom validator for the to and error form fields
def toValidator(form, field):
    message = "Input must follow following pattern: [function, conditional, arguments (optional)]"
    if field.data != None:
        data = field.data.split(",")
        if len(data) < 2:
            raise ValidationError(message)


#Custom validator for the In form field
def inValidator(form, field):
    message = "Input must be JSON"
    try:
        data = json.loads(field.data)
    except:
        raise ValidationError(message)
