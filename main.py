from flask import Flask, request
from google.cloud import datastore
import json

app = Flask(__name__)
client = datastore.Client()

# Class to wrap DB functions
class Database:
    def __init__(self):
        self.client = datastore.Client()
        
    def _get_command_stack_key(self, stack_type):
        return client.key('CommandStack', stack_type)
    
    def _get_variable_key(self, name):
        return client.key('Variable', name)
        
    def _push_command(self, command_type, name, old_value, new_value):
        undo_stack_key = self._get_command_stack_key('undo')
        undo_stack = datastore.Entity(undo_stack_key)
        existing = client.get(undo_stack_key)
        commands = existing['commands'] if existing else []
        commands.append({
            'type': command_type,
            'name': name,
            'old_value': old_value,
            'new_value': new_value
        })
        undo_stack.update({'commands': commands})
        client.put(undo_stack)
        
        # Clear redo stack
        redo_stack_key = self._get_command_stack_key('redo')
        if client.get(redo_stack_key):
            client.delete(redo_stack_key)

    def set(self, name, value):
        var_key = self._get_variable_key(name)
        var = client.get(var_key)
        old_value = None if var is None else var['value']
        
        new_var = datastore.Entity(var_key)
        new_var.update({'value': value})
        client.put(new_var)
        
        self._push_command('SET', name, old_value, value)
        return f"{name} = {value}"

    def get(self, name):
        var_key = self._get_variable_key(name)
        var = client.get(var_key)
        return str(var['value']) if var else "None"

    def unset(self, name):
        var_key = self._get_variable_key(name)
        var = client.get(var_key)
        if var:
            old_value = var['value']
            client.delete(var_key)
            self._push_command('UNSET', name, old_value, None)
        return f"{name} = None"

    def numequalto(self, value):
        query = client.query(kind='Variable')
        query.add_filter('value', '=', value)
        count = len(list(query.fetch()))
        return str(count)

    def undo(self):
        undo_stack_key = self._get_command_stack_key('undo')
        undo_stack = client.get(undo_stack_key)
        
        if not undo_stack or not undo_stack.get('commands', []):
            return "NO COMMANDS"
            
        commands = undo_stack['commands']
        command = commands.pop()
        
        # Update undo stack
        new_undo_stack = datastore.Entity(undo_stack_key)
        new_undo_stack.update({'commands': commands})
        client.put(new_undo_stack)
        
        # Update redo stack
        redo_stack_key = self._get_command_stack_key('redo')
        redo_stack = client.get(redo_stack_key)
        new_redo_stack = datastore.Entity(redo_stack_key)
        redo_commands = redo_stack['commands'] if redo_stack else []
        redo_commands.append(command)
        new_redo_stack.update({'commands': redo_commands})
        client.put(new_redo_stack)
        
        var_key = self._get_variable_key(command['name'])
        
        if command['type'] == 'SET':
            if command['old_value'] is None:
                client.delete(var_key)
            else:
                var = datastore.Entity(var_key)
                var.update({'value': command['old_value']})
                client.put(var)
        elif command['type'] == 'UNSET':
            var = datastore.Entity(var_key)
            var.update({'value': command['old_value']})
            client.put(var)
            
        # Get current value after undo
        current_var = client.get(var_key)
        current_value = current_var['value'] if current_var else None
        return f"{command['name']} = {current_value if current_value is not None else 'None'}"

    def redo(self):
        redo_stack_key = self._get_command_stack_key('redo')
        redo_stack = client.get(redo_stack_key)
        
        if not redo_stack or not redo_stack.get('commands', []):
            return "NO COMMANDS"
            
        commands = redo_stack['commands']
        command = commands.pop()
        
        # Update redo stack
        new_redo_stack = datastore.Entity(redo_stack_key)
        new_redo_stack.update({'commands': commands})
        client.put(new_redo_stack)
        
        # Update undo stack
        undo_stack_key = self._get_command_stack_key('undo')
        undo_stack = client.get(undo_stack_key)
        new_undo_stack = datastore.Entity(undo_stack_key)
        undo_commands = undo_stack['commands'] if undo_stack else []
        undo_commands.append(command)
        new_undo_stack.update({'commands': undo_commands})
        client.put(new_undo_stack)
        
        if command['type'] == 'SET':
            var_key = self._get_variable_key(command['name'])
            var = datastore.Entity(var_key)
            var.update({'value': command['new_value']})
            client.put(var)
            return f"{command['name']} = {command['new_value']}"
        elif command['type'] == 'UNSET':
            var_key = self._get_variable_key(command['name'])
            client.delete(var_key)
            return f"{command['name']} = None"

    def end(self):
        query = client.query(kind='Variable')
        variables = query.fetch()
        for var in variables:
            client.delete(var.key)
            
        client.delete(self._get_command_stack_key('undo'))
        client.delete(self._get_command_stack_key('redo'))
        return "CLEANED"

db = Database()

# Home Route
@app.route('/')
def home():
    return '''
        <h1>Welcome to the Simple DB App</h1>
        <p>Use the following commands to interact with the app:</p>
        <ul>
            <li><strong>/set?name={variable_name}&value={variable_value}</strong> - Set a variable</li>
            <li><strong>/get?name={variable_name}</strong> - Get the value of a variable</li>
            <li><strong>/unset?name={variable_name}</strong> - Unset a variable</li>
            <li><strong>/numequalto?value={variable_value}</strong> - Count how many variables have a specific value</li>
            <li><strong>/undo</strong> - Undo the last SET/UNSET operation</li>
            <li><strong>/redo</strong> - Redo the most recent undone operation</li>
            <li><strong>/end</strong> - Clean up all data</li>
            <li><strong>/history</strong> - Display history of commands</li>
        </ul>
    '''

# Set Route
@app.route('/set')
def set():
    name = request.args.get('name')
    value = request.args.get('value')
    if not name or not value:
        return "Invalid parameters", 400
    return db.set(name, value)

# Get Route
@app.route('/get')
def get():
    name = request.args.get('name')
    if not name:
        return "Invalid parameters", 400
    return db.get(name)

# Unset Route
@app.route('/unset')
def unset():
    name = request.args.get('name')
    if not name:
        return "Invalid parameters", 400
    return db.unset(name)

# Numequalto Route
@app.route('/numequalto')
def numequalto():
    value = request.args.get('value')
    if not value:
        return "Invalid parameters", 400
    return db.numequalto(value)

# Undo Route
@app.route('/undo')
def undo():
    return db.undo()

# Redo Route
@app.route('/redo')
def redo():
    return db.redo()

# End Route
@app.route('/end')
def end():
    return db.end()

# Debug and new feature to view history Route
@app.route('/history')
def get_history():
    undo_stack_key = db._get_command_stack_key('undo')
    undo_stack = client.get(undo_stack_key)
    if not undo_stack:
        return json.dumps([])
    return json.dumps(undo_stack['commands'])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)