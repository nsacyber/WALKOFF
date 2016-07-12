import json

def main(args, value):
    outputFormat = "str"
    if "outputFormat" in args:
        outputFormat = args["outputFormat"]
    try:
        output = []

        if isinstance(value, str):
            context = json.loads(value)

        for item in args["args"]:
            result = context
            for key in item:
                if isinstance(result, dict) or isinstance(result, list):
                    try:
                        result = result[int(key)] #Test to convert str number into integer

                    except Exception as e:
                        result = result[str(key)]

                else:
                    output.append(result)
            output.append(result)

        print output
        if outputFormat == "str":
            #If the list only has one member just output that value instead of that value enclosed within a useless list
            if len(args["args"]) == 1:
                return str(output[0])
            return str(output)
        else:
            return output

    except Exception as e:
        print e
        return None