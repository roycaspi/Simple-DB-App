Google App Engine Variable Database

This project is a simple key-value variable store implemented using Google App Engine (GAE) and Flask. It listens to HTTP requests and performs basic in-memory database operations using Google Cloud Datastore as a persistent backend.

The app supports CRUD operations for variables, as well as undo/redo functionality and value-based queries.

🌐 Live Demo

Hosted on: https://simple-db-app.lm.r.appspot.com

Replace your-app-id with your deployed App Engine app ID.

🚀 Features

✅ Set, Get, and Unset variables via HTTP

🔁 Undo/Redo of recent changes

🔍 Count how many variables equal a specific value

🧼 Cleanup all stored data via /end

🧾 History tracking of commands via /history

🧠 O(1) access operations using Datastore assumptions

🔗 API Endpoints

Endpoint

Description

Example Input

Example Output

/set

Sets a variable to a value

/set?name=x&value=10

x = 10

/get

Retrieves the value of a variable

/get?name=x

10 or None

/unset

Deletes a variable

/unset?name=x

x = None

/numequalto

Counts variables equal to a value

/numequalto?value=10

2 or 0

/undo

Reverts the last SET/UNSET command

/undo

x = 5 or NO COMMANDS

/redo

Re-applies the last undone command

/redo

x = 10 or NO COMMANDS

/end

Clears all variables and command stacks

/end

CLEANED

/history

Displays history of executed SET/UNSET commands

/history

JSON list of commands

📦 Technologies Used

Python 3

Flask (Web framework)

Google Cloud App Engine (Hosting)

Google Cloud Datastore (Storage)

📂 File Structure

variable-db/
├── main.py              # Main Flask app with all route handlers
├── app.yaml             # GAE configuration file
├── README.md            # Project documentation


🧪 Example Workflow

/set?name=a&value=100        → a = 100
/set?name=b&value=200        → b = 200
/numequalto?value=100        → 1
/unset?name=a                → a = None
/undo                        → a = 100
/redo                        → a = None
/get?name=a                  → None
/end                         → CLEANED

🧠 Bonus Feature: /history Endpoint

The app tracks and logs all SET and UNSET operations in a command stack. Access them with:

/history

This can help with debugging or understanding the state of variables over time.

🧑‍💻 Author

Roy CaspiFor questions, reach out or fork the project to contribute.

📄 License

This project is licensed under the MIT License.

Enjoy building with App Engine and Python! 🚀

