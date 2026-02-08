from flask import Flask, render_template, request
import subprocess
import tempfile
import os
import re

app = Flask(__name__)

WEKA_JAR = "weka.jar"
MODEL_FILE = "smoking_relapse.model"

def q(v):
    return f"'{v}'"


def parse_weka_output(output):
    for line in output.splitlines():
        if re.search(r"\d+:\?", line):

            # Predicted label
            pred_match = re.search(r"\d+:(YES|NO)", line)
            predicted = pred_match.group(1) if pred_match else None
    
            # Extract probabilities
            probs = [float(p.replace("*", "")) for p in re.findall(r"\*?\d+\.\d+", line)]

            # Class order: {'YES','NO'}
            yes_prob = probs[0] if len(probs) > 0 else 0.0
            no_prob  = probs[1] if len(probs) > 1 else 0.0

            # If only one prob exists, assign it to predicted class
            if len(probs) == 1 and predicted == "NO":
                no_prob = probs[0]
                yes_prob = 1 - probs[0]
            elif len(probs) == 1 and predicted == "YES":
                yes_prob = probs[0]
                no_prob = 1 - probs[0]

            return predicted, yes_prob, no_prob

    return None, 0.0, 0.0


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    yes_prob = None
    no_prob = None
    form_data = {}

    if request.method == "POST":
        form_data = request.form

        values = [
            q(form_data["Age"]),
            q(form_data["NumberOfSticksPerDay"]),
            q(form_data["Gender"]),
            q(form_data["CivilStatus"]),
            q(form_data["HasInfoAboutCessation"]),
            q(form_data["EmploymentStatus"]),
            q(form_data["Type"]),
            q(form_data["AgeStarted"]),
            q(form_data["Influence"]),
            q(form_data["Urge"]),
            q(form_data["MainAccess"]),
            "?"
        ]

        arff = f"""@relation SmokingRelapse

@attribute Age {{'Late Working Age','Mid Working Age','Pre-Senior','Young Adults','Under 18','Early Working Age'}}
@attribute NumberOfSticksPerDay {{'Medium Smoker','Heavy Smoker','Light Smoker'}}
@attribute Gender {{'M','F'}}
@attribute CivilStatus {{'Married','Single'}}
@attribute HasInfoAboutCessation {{'No','Yes'}}
@attribute EmploymentStatus {{'Employed','NotOfficeing','Officeing','Retired'}}
@attribute Type {{'RegularSmoker','SocialSmoker'}}
@attribute AgeStarted {{'Adolescence','Childhood','Young Adult'}}
@attribute Influence {{'Curiosity','FamilyInfluence','PeerPressure'}}
@attribute Urge {{'Stressed','Bored','Sad','Angry','Happy'}}
@attribute MainAccess {{'Home','Office','PublicPlace','Others','Bars'}}
@attribute Relapsed {{'YES','NO'}}

@data
{','.join(values)}
"""

        with tempfile.NamedTemporaryFile(delete=False, suffix=".arff") as f:
            f.write(arff.encode())
            test_file = f.name

        cmd = [
            "java", "-cp", WEKA_JAR,
            "weka.classifiers.bayes.NaiveBayesUpdateable",
            "-l", MODEL_FILE,
            "-T", test_file,
            "-p", "0"
        ]

        process = subprocess.run(cmd, capture_output=True, text=True)
        output = process.stdout

        result, yes_prob, no_prob = parse_weka_output(output)

        os.remove(test_file)

    return render_template(
        "index.html",
        result=result,
        yes_prob=yes_prob,
        no_prob=no_prob,
        form_data=form_data
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)