from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass


class CreateFormCommand(Command):
    def __init__(self, scene, parent_form=None, position=None):
        self.scene = scene
        self.parent_form = parent_form
        self.created_form = None
        self.position = position

    def execute(self):
        from form_widget import FormWidget
        from link_line import LinkLine
        self.created_form = FormWidget(parent=self.parent_form)
        self.scene.addItem(self.created_form)
        if self.position:
            self.created_form.setPos(self.position)
        if self.parent_form:
            self.parent_form.child_forms.append(self.created_form)
            link_line = LinkLine(self.parent_form, self.created_form)
            self.scene.addItem(link_line)
            self.created_form.link_line = link_line

    def undo(self):
        if self.created_form:
            self.scene.removeItem(self.created_form)
            if self.parent_form:
                self.parent_form.child_forms.remove(self.created_form)
                if self.created_form.link_line:
                    self.scene.removeItem(self.created_form.link_line)
            self.created_form = None


class DeleteFormCommand(Command):
    def __init__(self, form):
        self.form = form
        self.parent_form = form.parent_form
        self.child_forms = form.child_forms[:]
        self.link_line = form.link_line

    def execute(self):
        self.form.deleteForm()

    def undo(self):
        self.form.scene().addItem(self.form)
        if self.parent_form:
            self.parent_form.child_forms.append(self.form)
        self.form.child_forms = self.child_forms
        if self.link_line:
            self.form.scene().addItem(self.link_line)
            self.form.link_line = self.link_line


class MoveFormCommand(Command):
    def __init__(self, form, old_pos, new_pos):
        self.form = form
        self.old_pos = old_pos
        self.new_pos = new_pos

    def execute(self):
        self.form.setPos(self.new_pos)
        if self.form.link_line:
            self.form.link_line.updatePosition()

    def undo(self):
        self.form.setPos(self.old_pos)
        if self.form.link_line:
            self.form.link_line.updatePosition()
