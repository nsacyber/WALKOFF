from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def default():
    return render_template("debugTools.html")

@app.route("/workflow/", methods=['GET'])
def workflow():
    return ""



if __name__ == "__main__":
    app.run()