import json
import os


def convert_workflows():
    for subdir, dir, files in os.walk("."):
        for file in files:
            if ".playbook" in file:
                print("Processing {}".format(file))
                with open(os.path.join(subdir, file), "r") as f:
                    playbook = json.load(f)
                    for workflow in playbook['workflows']:
                        workflow["next_steps"] = []
                        for step in workflow['steps']:
                            if "next_steps" in step:
                                next_steps = step.pop("next_steps")
                                for next_step in next_steps:
                                    next_step["source_uid"] = step["uid"]
                                    dst = next_step.pop("name")
                                    next_step["destination_uid"] = dst
                                    workflow["next_steps"].append(next_step)
                with open(os.path.join(subdir, file), "w") as f:
                    json.dump(playbook, f, sort_keys=True, indent=4, separators=(',', ': '))

if __name__ == "__main__":
    convert_workflows()
