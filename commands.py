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
        self.link_line = None

    def execute(self):
        from form_widget import FormWidget
        from link_line import LinkLine
        self.created_form = FormWidget(parent=self.parent_form)
        self.scene.addItem(self.created_form)
        if self.position:
            self.created_form.setPos(self.position)
        if self.parent_form:
            self.parent_form.child_forms.append(self.created_form)
            self.link_line = LinkLine(self.parent_form, self.created_form)
            self.scene.addItem(self.link_line)
            self.created_form.link_line = self.link_line

    def undo(self):
        if self.created_form:
            if self.created_form.scene() == self.scene:
                self.scene.removeItem(self.created_form)
            if self.parent_form and self.created_form in self.parent_form.child_forms:
                self.parent_form.child_forms.remove(self.created_form)
            if self.link_line and self.link_line.scene() == self.scene:
                self.scene.removeItem(self.link_line)
            self.created_form = None
            self.link_line = None


class DeleteFormCommand(Command):
    def __init__(self, form):
        self.form = form
        self.parent_form = form.parent_form
        self.child_forms = form.child_forms[:]
        self.link_line = form.link_line
        self.scene = form.scene()
        self.pos = form.pos()
        self.deleted_subtree = []

    def execute(self):
        self.deleted_subtree = self._delete_subtree(self.form)
        if self.parent_form and self.form in self.parent_form.child_forms:
            self.parent_form.child_forms.remove(self.form)

    def undo(self):
        self._restore_subtree(self.deleted_subtree)
        if self.parent_form:
            self.parent_form.child_forms.append(self.form)

    def _delete_subtree(self, form):
        deleted = []
        for child in form.child_forms[:]:
            deleted.extend(self._delete_subtree(child))

        if form.scene() == self.scene:
            self.scene.removeItem(form)
        if form.link_line and form.link_line.scene() == self.scene:
            self.scene.removeItem(form.link_line)

        deleted.append((form, form.pos(), form.link_line))
        return deleted

    def _restore_subtree(self, deleted_items):
        for form, pos, link_line in reversed(deleted_items):
            self.scene.addItem(form)
            form.setPos(pos)
            if link_line:
                self.scene.addItem(link_line)
                form.link_line = link_line


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
