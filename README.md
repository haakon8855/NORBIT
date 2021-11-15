# NORBIT Proximitiy Based RTLS Backend

## Installation guide
To install and run the backend, follow the steps below.
It is important to note that an env.py file, containing authentication
information, is required for accessing both NORBIT’s and our database.
Without this file the back-end server will not work.

### Requirements
- Python 3.7 or newer

### Installation steps
After navigating to the desired folder in your terminal, run the following
commands to start the project:  

    git clone https://github.com/haakon8855/NORBIT-backend.git
    cd NORBIT-backend
    python3 -m pip install pipenv
    python3 -m pipenv install

Lastly, to start the backend server, run  

    python3 main.py

Remember to have the env.py file ready. A tunnel is also required to access the database.
