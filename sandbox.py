import subprocess
import os
from dotenv import load_dotenv


load_dotenv()


def create_obs_script():
    USERNAME = str(os.getenv("NAME"))
    PASSWORD = str(os.getenv("PASSWORD"))

    with open("obs_script_template") as t, open("obs_script.py", "w") as f:
        for line in t:
            
            match line:
                case "# username =\n":
                    line = "username = \"" + USERNAME + "\"\n"
                case "# password =\n":
                    line = "password = \"" + PASSWORD + "\"\n"

            f.write(line)


create_obs_script()
