from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
from sqlalchemy.orm import Session

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/checklist'
db = SQLAlchemy(app)
CORS(app, resources={r"/*": {"origins": "*"}})

# Crie uma sessão do SQLAlchemy usando a instância db
session = Session(db)

class Checklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    tipo_equipamento = db.Column(db.String(50))
    tasks = db.relationship('Task', backref='checklist', lazy=True)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'), nullable=True)
    
class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255))
    checklists = db.relationship('Checklist', backref='template', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255))
    verificado = db.Column(db.Boolean, default=False)
    foto_verificado = db.Column(db.Boolean)
    checklist_id = db.Column(db.Integer, db.ForeignKey('checklist.id'), nullable=False)

# checklist = session.get(Checklist, id)

@app.route('/checklists', methods=['GET'])
@cross_origin() 
def get_checklists():
    checklists = Checklist.query.all()
    checklist_list = []
    for checklist in checklists:
        checklist_data = {
            'id': checklist.id,
            'name': checklist.name,
            'tipo_equipamento': checklist.tipo_equipamento,
            'tasks': [{'id': task.id, 'description': task.description, 'verificado': task.verificado, 'foto_verificado': task.foto_verificado} for task in checklist.tasks]
        }
        checklist_list.append(checklist_data)
    return jsonify({'checklists': checklist_list})

@app.route('/checklists/<int:id>', methods=['GET'])
@cross_origin() 
def get_checklist(id):
    checklist = Checklist.query.get(id)
    if checklist is None:
        return jsonify({'error': 'Checklist not found'}), 404
    checklist_data = {
        'id': checklist.id,
        'name': checklist.name,
        'tipo_equipamento': checklist.tipo_equipamento,
        'tasks': [{'id': task.id, 'description': task.description, 'verificado': task.verificado, 'foto_verificado': task.foto_verificado} for task in checklist.tasks]
    }
    return jsonify(checklist_data)

@app.route('/checklists', methods=['POST'])
@cross_origin() 
def create_checklist():
    data = request.json
    name = data.get('name')
    tipo_equipamento = data.get('tipo_equipamento')
    tasks_data = data.get('tasks', [])

    checklist = Checklist(name=name, tipo_equipamento=tipo_equipamento)
    
    for task_data in tasks_data:
        description = task_data.get('description')
        verificado = task_data.get('verificado', False)
        foto_verificado = task_data.get('foto_verificado', False)
        task = Task(description=description, verificado=verificado, foto_verificado=foto_verificado)
        checklist.tasks.append(task)

    db.session.add(checklist)
    db.session.commit()
    return jsonify({'message': 'Checklist created successfully'}), 201


@app.route('/checklists/<int:id>', methods=['PUT'])
@cross_origin()
def update_checklist(id):
    # Retrieve the checklist from the database
    checklist = Checklist.query.get(id)
    if checklist is None:
        return jsonify({'error': 'Checklist not found'}), 404

    # Parse JSON data from the request
    data = request.json

    # Update checklist attributes
    checklist.name = data.get('name')
    checklist.tipo_equipamento = data.get('tipo_equipamento')

    # Create a list to keep track of updated tasks
    updated_tasks = []

    # Iterate over the task data in the request
    for task_data in data.get('tasks', []):
        task_id = task_data.get('id')
        description = task_data.get('description')
        verificado = task_data.get('verificado')
        foto_verificado = task_data.get('foto_verificado')

        # If a task ID is provided, update the existing task
        if task_id:
            task = Task.query.get(task_id)
            if task:
                task.description = description
                task.verificado = verificado
                task.foto_verificado = foto_verificado
        else:
            # If no task ID is provided, create a new task
            task = Task(description=description, verificado=verificado, foto_verificado=foto_verificado)
            checklist.tasks.append(task)

        updated_tasks.append(task)

    # Remove tasks that are no longer in the updated_tasks list
    for task in checklist.tasks:
        if task not in updated_tasks:
            db.session.delete(task)

    # Commit the changes to the database
    db.session.commit()

    return jsonify({'message': 'Checklist updated successfully'})



@app.route('/checklists/<int:id>', methods=['DELETE'])
@cross_origin() 
def delete_checklist(id):
    try:
        # Verifica se o checklist com o ID fornecido existe no banco de dados
        checklist = Checklist.query.get(id)
        if checklist is None:
            return jsonify({'error': 'Checklist not found'}), 404

        # Remove todas as tarefas associadas a este checklist
        for task in checklist.tasks:
            db.session.delete(task)

        # Se o checklist foi encontrado e todas as tarefas foram removidas, exclua-o
        db.session.delete(checklist)
        db.session.commit()
        
        return jsonify({'message': 'Checklist and associated tasks deleted successfully'})
    except Exception as e:
        # Em caso de erro, registre a exceção para depuração
        error_message = f"An error occurred while deleting the checklist: {str(e)}"
        return jsonify({'error': error_message}), 500


# Rotas de Templates
@app.route('/templates', methods=['GET'])
@cross_origin() 
def get_templates():
    templates = Template.query.all()
    template_list = []

    for template in templates:
        template_data = {
            'id': template.id,
            'nome': template.nome,
        }
        # Adicione a lista de checklists somente se houver checklists associados ao template
        if template.checklists:
            template_data['checklists'] = [{'id': checklist.id, 'name': checklist.name} for checklist in template.checklists]

        template_list.append(template_data)

    return jsonify({'templates': template_list})


@app.route('/templates/<int:id>', methods=['GET'])
@cross_origin() 
def get_template(id):
    template = Template.query.get(id)
    if template is None:
        return jsonify({'error': 'Template not found'}), 404
    template_data = {
        'id': template.id,
        'nome': template.nome,
        'checklists': [{'id': checklist.id, 'name': checklist.name} for checklist in template.checklists]
    }
    return jsonify(template_data)

@app.route('/templates', methods=['POST'])
@cross_origin() 
def create_template():
    data = request.json
    nome = data.get('nome')
    checklists_data = data.get('checklists', [])

    template = Template(nome=nome)

    for checklist_data in checklists_data:
        checklist_id = checklist_data.get('id')
        checklist = Checklist.query.get(checklist_id)
        if checklist:
            template.checklists.append(checklist)

    db.session.add(template)
    db.session.commit()
    return jsonify({'message': 'Template created successfully'}), 201

@app.route('/templates/<int:id>', methods=['PUT'])
@cross_origin() 
def update_template(id):
    template = Template.query.get(id)
    if template is None:
        return jsonify({'error': 'Template not found'}), 404

    data = request.json
    template.nome = data.get('nome')

    # Atualize a lista de checklists associados ao template
    updated_checklists = []
    for checklist_data in data.get('checklists', []):
        checklist_id = checklist_data.get('id')
        checklist = Checklist.query.get(checklist_id)
        if checklist:
            updated_checklists.append(checklist)

    template.checklists = updated_checklists

    db.session.commit()
    return jsonify({'message': 'Template updated successfully'})

@app.route('/templates/<int:id>', methods=['DELETE'])
@cross_origin() 
def delete_template(id):
    template = Template.query.get(id)
    if template is None:
        return jsonify({'error': 'Template not found'}), 404

    db.session.delete(template)
    db.session.commit()
    return jsonify({'message': 'Template deleted successfully'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='192.168.4.36', port=5000,debug=True)