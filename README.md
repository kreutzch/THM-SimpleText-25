# Setting up

* Install Docker on your system
* Ensure Docker is running on your system and log in to Docker in your terminal
* Clone this repository
* Use your terminal, go to the folder where this `README` is located
* Run `./gen_env.sh ` in your terminal to create a file containing some environmental variables
* Build Docker container from cloned repository:

`docker build -t text_simplification . `

* Actually launch the Docker container:

`docker compose up -d`

* Download data from SimpleText'25 google drive for track 1.1 and put extracted data in folder `workspace/data`
* Put your OpenAI key in file ``workspace/OpenAI_token.txt`
* Put your Gemini key in file `workspace/Gemini_token.txt`
* Use IDE of your choice, attach to the Docker container

# Running
* Run `complex_term_identification.ipynb`
* Run `THM_runner.py`
