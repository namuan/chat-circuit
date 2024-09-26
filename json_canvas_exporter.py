import json
import uuid

from form_widget import FormWidget


class JsonCanvasExporter:
    def __init__(self, scene):
        self.scene = scene

    def export(self, file_name):
        nodes = []
        edges = []
        form_ids = {}

        for i, item in enumerate(self.scene.items()):
            if isinstance(item, FormWidget) and not item.parent_form:
                form_id = str(uuid.uuid4())
                form_ids[item] = form_id
                nodes.append(self.form_to_json_canvas_node(item, form_id))
                self.export_child_forms(item, form_id, nodes, edges, form_ids)

        canvas_data = {"nodes": nodes, "edges": edges}

        with open(file_name, "w") as f:
            json.dump(canvas_data, f, indent=2)

    def export_child_forms(self, form, parent_id, nodes, edges, form_ids):
        for child in form.child_forms:
            child_id = str(uuid.uuid4())
            form_ids[child] = child_id
            nodes.append(self.form_to_json_canvas_node(child, child_id))
            edges.append(self.create_edge(parent_id, child_id))
            self.export_child_forms(child, child_id, nodes, edges, form_ids)

    def form_to_json_canvas_node(self, form, form_id):
        rect = form.mapToScene(form.boundingRect()).boundingRect()
        x = int(rect.x())
        y = int(rect.y())
        width = int(rect.width())
        height = int(rect.height())

        return {
            "id": form_id,
            "type": "text",
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "text": form.input_box.widget().toPlainText()
            + "\n\n"
            + form.conversation_area.widget().toPlainText(),
        }

    def create_edge(self, source_id, target_id):
        edge_id = str(uuid.uuid4())
        return {
            "id": edge_id,
            "fromNode": source_id,
            "toNode": target_id,
        }
